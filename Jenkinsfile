pipeline {
    agent {
        label 'linux-py-docker'
    }
    environment {
        SESSION_NAME = "ami-general-session"
        REGION = "us-east-1"
        BASE_AMI = "ami-01816d07b1128cd2d"
    }
    stages {
        stage('Debug Key Creation') {
            steps {
                withCredentials([file(credentialsId: 'private-key-ami', variable: 'PRIVATE_KEY')]) {
                    // Check if the private key file is created
                    sh 'ls -l $PRIVATE_KEY || echo "Key not created!"'
                }
            }
        }
        stage('Run Python Script') {
            steps {
                withCredentials([
                    file(credentialsId: 'private-key-ami', variable: 'PRIVATE_KEY'),
                    string(credentialsId: 'subnet-id', variable: 'SUBNET_ID'),
                    string(credentialsId: 'security-group-id', variable: 'SECURITY_GROUP_ID')
                ]) {
                    // Use the private key in SSH
                    sh '''
                    cp $PRIVATE_KEY ~/.ssh/id_rsa
                    chmod 600 ~/.ssh/id_rsa

                    python3 ./create_ami.py \
                      --base_ami $BASE_AMI \
                      --ami_name jenkins-linux-py-docker-${BUILD_NUMBER} \
                      --region $REGION \
                      --subnet_id $SUBNET_ID \
                      --security_group $SECURITY_GROUP_ID \
                      --key_name 'jenkins-linux' \
                      --key_path ~/.ssh/id_rsa
                    '''
                }
            }
        }
    }
}
