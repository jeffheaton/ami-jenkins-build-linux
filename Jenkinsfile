pipeline {
    agent {
        label 'linux-py-docker'
    }
    stages {
        stage('Build AWS AMI') {
            steps {
                sh 'echo "Hello from EC2 node!"'
            }
        }
    }
}