# AWS EC2 Setup

Here's the installation process to make sure your environment is ready to run the Airbyte connector service:

**Connect to your Amazon Linux 2 instance**:
   Use SSH to connect to your instance:
   ```bash
   ssh -i "your-key-pair.pem" ec2-user@your-instance-ip-or-dns
   ```

**Update the installed packages and package cache**:
   ```bash
   sudo yum update -y
   ```

**Install `openssl11`, `awslogs`, and Python 3**:
   ```bash
   sudo yum install -y openssl11 awslogs python3
   ```

**Install Docker via Amazon Linux Extras**:
   ```bash
   sudo amazon-linux-extras install docker
   ```

 **Start the Docker service**:
   ```bash
   sudo service docker start
   ```

**Enable Docker to start on boot**:
   ```bash
   sudo systemctl enable docker
   ```

**Start, enable, and configure the `awslogs` service**:
   The `awslogs` agent sends logs to CloudWatch Logs.
   ```bash
   sudo systemctl start awslogsd
   sudo systemctl enable awslogsd.service
   ```

**Start and enable the `cron` service**:
   ```bash
   sudo systemctl start crond
   sudo systemctl enable crond
   ```

**Add the `ec2-user` to the Docker group**:
   This allows the `ec2-user` to run Docker commands without using `sudo`. After adding `ec2-user` to the Docker group, it's recommended to log out and log back in to ensure your user has the correct permissions.
   ```bash
   sudo usermod -a -G docker ec2-user
   ```
 **Verify the installation of Python 3**
   ```bash
   python3 --version
   pip3 --version
   ```

**Install Python Package via pip3**:
   ```bash
   pip3 install docker boto3 psutil croniter 'urllib3<=1.26.15'
   ```

After completing these steps, you will have Docker, `openssl11`, `awslogs`, `Python 3`, and `pip3` installed. Additionally, the Docker, `awslogs`, and `cron` services will be set to start on boot.

That's it!