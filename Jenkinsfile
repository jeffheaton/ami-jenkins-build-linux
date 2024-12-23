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
        stage('Setup Environment') {
            steps {
                sh '''
                # Install boto3
                sudo pip3 install boto3
                '''
            }
        }
        stage('Assume AWS Role') {
            steps {
                withCredentials([
                    string(credentialsId: 'jenkins-role-build-ami-linux-general', variable: 'ROLE_ARN')
                ]) {
                    script {
                        def assumeRoleOutput = sh(
                            script: """
                            aws sts assume-role \
                              --role-arn "$ROLE_ARN" \
                              --role-session-name "$SESSION_NAME" \
                              --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
                              --output text
                            """,
                            returnStdout: true
                        ).trim()

                        if (!assumeRoleOutput) {
                            error "Failed to assume role: $ROLE_ARN"
                        }

                        def creds = assumeRoleOutput.split()
                        withEnv([
                            "AWS_ACCESS_KEY_ID=${creds[0]}",
                            "AWS_SECRET_ACCESS_KEY=${creds[1]}",
                            "AWS_SESSION_TOKEN=${creds[2]}"
                        ]) {
                            echo "AWS Role assumed successfully."
                        }
                    }
                }
            }
        }
        stage('Run Python Script') {
            steps {
                withCredentials([
                    file(credentialsId: 'jenkins-aws-key', variable: 'PRIVATE_KEY_PATH'),
                    string(credentialsId: 'private-subnet-id', variable: 'SUBNET_ID'),
                    string(credentialsId: 'ssh-security-group-id', variable: 'SECURITY_GROUP_ID')
                ]) {
                    sh """
                    python3 ./create_ami.py \
                    --base_ami "${BASE_AMI}" \
                    --ami_name "jenkins-linux-py-docker-${BUILD_NUMBER}" \
                    --region "${REGION}" \
                    --subnet_id "${SUBNET_ID}" \
                    --security_group "${SECURITY_GROUP_ID}" \
                    --key_name "jenkins-linux" \
                    --key_path "${PRIVATE_KEY_PATH}"
                    """
                }
            }
        }
    }
}
