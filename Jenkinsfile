pipeline {
    agent {
        label 'aws-ec2-linux'
    }
    stages {
        stage('Build AWS AMI') {
            steps {
                sh 'echo "Hello from EC2 node!"'
            }
        }
    }
}