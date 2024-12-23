pipeline {
    agent {
        label 'linux-py-docker'
    }
    environment {
        SESSION_NAME = "ami-general-session"
        REGION = "us-east-1"
        BASE_AMI = "ami-01816d07b1128cd2d" // Moved to a constant for clarity
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
                    string(credentialsId: 'role-arn', variable: 'ROLE_ARN') // Securely inject ROLE ARN
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

                        // Check for errors in the output
                        if (!assumeRoleOutput) {
                            error "Failed to assume role: $ROLE_ARN"
                        }

                        // Parse credentials
                        def creds = assumeRoleOutput.split()
                        env.AWS_ACCESS_KEY_ID = creds[0]
                        env.AWS_SECRET_ACCESS_KEY = creds[1]
                        env.AWS_SESSION_TOKEN = creds[2]
                    }
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
                    sh '''
                    git clone https://github.com/jeffheaton/ami-jenkins-build-linux.git
                    cd ami-jenkins-build-linux

                    python3 ./create_ami.py \
                      --base_ami $BASE_AMI \
                      --ami_name jenkins-linux-py-docker-${BUILD_NUMBER} \
                      --region $REGION \
                      --subnet_id $SUBNET_ID \
                      --security_group $SECURITY_GROUP_ID \
                      --key_name "jenkins-linux" \
                      --key_path $PRIVATE_KEY
                    '''
                }
            }
        }
    }
}
