// ===========================================================================
//  Jenkins Declarative Pipeline  —  MovieLens CI/CD
//  GitHub (push)  ->  Jenkins (EC2 #1)  ->  rsync/SSH deploy  ->  App (EC2 #2)
//
//  Triggered automatically by a GitHub webhook on every push (see "triggers").
//  Three required stages: Build, Test, Deploy.
// ===========================================================================

pipeline {
    agent any

    // ---- Configuration -----------------------------------------------------
    environment {
        // The PRIVATE IP of the application EC2 instance (EC2 #2) inside the VPC.
        APP_SERVER   = '10.0.1.20'          // <-- replace with EC2 #2 private IP
        APP_USER     = 'ubuntu'             // 'ubuntu' (Ubuntu) or 'ec2-user' (Amazon Linux)
        APP_DIR      = '/opt/movielens'     // where the app lives on EC2 #2
        SERVICE_NAME = 'movielens'          // systemd service name
        VENV         = '/opt/movielens/venv'
    }

    // ---- Auto-trigger on every GitHub push --------------------------------
    triggers {
        githubPush()
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        // 1. BUILD ----------------------------------------------------------
        //    Fetch code (done implicitly by SCM), create a virtualenv,
        //    install dependencies — prepare the app for deployment.
        stage('Build') {
            steps {
                echo '===== BUILD: installing dependencies ====='
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    echo "Build complete. Installed packages:"
                    pip list
                '''
            }
        }

        // 2. TEST -----------------------------------------------------------
        //    Run pytest against the bundled dataset (no AWS needed).
        stage('Test') {
            steps {
                echo '===== TEST: running pytest ====='
                sh '''
                    . .venv/bin/activate
                    pytest -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        // 3. DEPLOY ---------------------------------------------------------
        //    Copy the app to EC2 #2 and (re)start it as a systemd service.
        //    'app-server-ssh' is the SSH private-key credential stored in Jenkins.
        stage('Deploy') {
            steps {
                echo '===== DEPLOY: shipping to app server (EC2 #2) ====='
                sshagent(credentials: ['app-server-ssh']) {
                    sh '''
                        # Ensure target dir exists
                        ssh -o StrictHostKeyChecking=no ${APP_USER}@${APP_SERVER} \
                            "sudo mkdir -p ${APP_DIR} && sudo chown -R ${APP_USER}:${APP_USER} ${APP_DIR}"

                        # Sync code (exclude local venv / git / caches)
                        rsync -avz --delete \
                            --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
                            --exclude 'test-results.xml' \
                            ./ ${APP_USER}@${APP_SERVER}:${APP_DIR}/

                        # Install deps + restart the service on the app server
                        ssh -o StrictHostKeyChecking=no ${APP_USER}@${APP_SERVER} '
                            cd '"${APP_DIR}"' &&
                            python3 -m venv '"${VENV}"' &&
                            '"${VENV}"'/bin/pip install --upgrade pip &&
                            '"${VENV}"'/bin/pip install -r requirements.txt &&
                            sudo systemctl restart '"${SERVICE_NAME}"' &&
                            sleep 3 &&
                            sudo systemctl --no-pager status '"${SERVICE_NAME}"' &&
                            curl -fs http://localhost:5000/health
                        '
                    '''
                }
            }
        }
    }

    post {
        success { echo '✅ Pipeline SUCCEEDED — app deployed to EC2 #2.' }
        failure { echo '❌ Pipeline FAILED — check the stage logs above.' }
        always  { echo "Build #${env.BUILD_NUMBER} finished with status: ${currentBuild.currentResult}" }
    }
}
