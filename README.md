# jenkins-build-linux

The AMI that I use in Jenkins for most of my Python and Docker builds that can be done in Linux

```
python script.py \
  --base_ami ami-01816d07b1128cd2d \
  --ami_name "my-private-ami" \
  --region us-east-1 \
  --subnet_id subnet-12345678 \
  --security_group sg-12345678 \
  --key_name my-key-pair \
  --key_path /path/to/my-key.pem
```
