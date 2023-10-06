import json
import time
import subprocess
import argparse
import os
import sys
import logging

from jinja2 import Template
import sqlite3
import boto3
import psutil
import croniter


RESOURCE_THRESHOLD = 80  # 80%

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

TASK_COMMAND = """sudo python3 {{ base }}/run.py \
                    -i {{ source_image }} \
                    -w {{ dest_image }} \
                    -s {{ configs }}/{{ id }}/source.json \
                    -d {{ configs }}/{{ id }}/destination.json \
                    -c {{ configs }}/{{ id }}/catalog.json \
                    {% if state_loc -%}-t {{ state_loc }} \
                    {% endif -%}-o {{ output }}/{{ id }} \
                    >> {{ output }}/{{ id }}/out.log """


class Scheduler(object):
    def __init__(self, s3_config_path):
        self.s3_client = boto3.client('s3')
        # Download config from S3
        self.config = self.get_config(s3_config_path)
        self.tasks = self.config.get('tasks')
        self.conn = sqlite3.connect(os.getcwd() + '/scheduler.db')
        self.conn.row_factory = sqlite3.Row  # Return dict instead of tuple
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS task_run_time (name TEXT, time INTEGER)")
        self.conn.commit()

    def get_config(self, s3_config_path):
        return json.loads(self.s3_client.get_object(
            Bucket=s3_config_path.split('/')[2],
            Key='/'.join(s3_config_path.split('/')[3:])
        )['Body'].read().decode('utf-8'))

    def is_task_running(self, task_command):
        for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if task_command in ' '.join(process.cmdline()):
                return True
        return False

    def system_resources_below_threshold(self):
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        return cpu_usage < RESOURCE_THRESHOLD and memory_info.percent < RESOURCE_THRESHOLD

    def download_configs(self, task):
        for name, path in task.get('configs').items():
            self.s3_client.download_file(
                Bucket=path.split('/')[2],
                Key='/'.join(path.split('/')[3:]),
                Filename=f"{self.config['dirs']['configs']}/{task['name'].split('-')[-1]}/{name}.json"
            )

    def _get_max_state_from_manifest(self, manifest_loc, task_id):
        if not os.path.exists(manifest_loc):
            return {}
        with open(manifest_loc, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            states = manifest.get(task_id, [])
            if not states:
                return {}
            max_state = {}
            for state in states:
                if not max_state:
                    max_state = state
                elif state['timestamp'] > max_state['timestamp']:
                    max_state = state
        return max_state['state_file_path']

    def _confirm_dirs_exist(self, dirs):
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def _render_task_cmd(self, task, state):
        task_args = {
            'id': task['id'],
            'source_image': task['source_image'],
            'dest_image': task['dest_image'],
            'output': self.config['dirs']['output'],
            'base': self.config['dirs']['base'],
            'configs': self.config['dirs']['configs'],
            'state_loc': state.get('path')
        }
        return Template(TASK_COMMAND).render(task_args)

    def execute_task(self, task, state_loc):
        if self.is_task_running(self._render_task_cmd(task, state_loc)):
            logger.info("Task already running")
            return 2
        while not self.system_resources_below_threshold():
            logger.info("System resources above threshold, waiting")
            time.sleep(10)  # Wait for 10 seconds before rechecking

        # Confirm download path exists on file system
        config_path = f"{self.config['dirs']['configs']}/{task['id']}"
        output_path = f"{self.config['dirs']['output']}/{task['id']}"
        self._confirm_dirs_exist([config_path, output_path])

        # Download configs from S3
        self.download_configs(task)

        # Render command
        command = self._render_task_cmd(task, state_loc)
        logger.debug(f"Running command: {command}")
        result = subprocess.run(command, check=True, shell=True, capture_output=True, text=True)
        logger.debug(f"{task['name']} stdout: {result.stdout}")
        logger.debug(f"{task['name']} stderr: {result.stderr}")
        return result.returncode

    def run(self):
        logger.info("Initializing OB Airbyte task runner")
        for task in self.tasks:
            if task.get('enabled'):
                logger.info("Checking task: %s", task['name'])
                # Get last run time
                self.cursor.execute("SELECT MAX(time) as last_run_time FROM task_run_time WHERE name = ?", (task.get('name'),))
                res = self.cursor.fetchone()
                if res and res['last_run_time']:
                    logger.debug("Last run time: %s", res['last_run_time'])
                    last_run_time = res['last_run_time']
                else:
                    logger.info("Last run time not set")
                    last_run_time = 0
                # Check task schedule
                # If it should have run but hasn't, run it
                current_time = time.time()
                cron = croniter.croniter(task.get('schedule'), current_time)
                if cron.get_prev() >= last_run_time:
                    logger.debug("Task is scheduled to run")
                    logger.debug("Running task: %s", task.get('name'))
                    
                    # Determine correct state path from manifest
                    state_loc = self._get_max_state_from_manifest(f"{self.config['dirs']['base']}/manifest.json", task['id'])
                    if self.is_task_running(self._render_task_cmd(task, state_loc)):
                        logger.debug("Task already running")
                        return 2
                    self.execute_task(task, state_loc)

                    # Update last run time
                    logger.debug("Updating last run time")
                    self.cursor.execute("INSERT INTO task_run_time VALUES (?, ?)", (task.get('name'), current_time))
                    self.conn.commit()
                    logger.debug(f"{task.get('name')} completed successfully")
                else:
                    logger.debug("Task not scheduled to run")
        logger.debug("OB Airbyte task runner finished")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='S3 path to config file', required=True)
    args = parser.parse_args()
    Scheduler(args.config).run()