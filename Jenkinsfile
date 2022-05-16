REGISTRY = "gcr.io/px_docker_repo/pxtask"

pipeline {

  agent { label 'prd-2-9' }

  stages {

    stage("build") {
      steps {
        script {
          def tag = env.BRANCH_NAME == "master" ? "prd" : "dev"
          buildTag = sh(returnStdout: true, script: "git rev-parse --short HEAD").trim() + "-" + tag
          echo "Build tag ${buildTag}"
          dockerImageName = REGISTRY + ":" + buildTag
          dockerImage = docker.build(dockerImageName, "--build-arg BUILDTAG=" + buildTag + " .")
        }
      }
    }

    stage("publish") {
     when {
       branch "master"
     }
      steps {
        script {
          docker.withRegistry('http://gcr.io', 'gcr:jewjonny-docker-repo') {
            dockerImage.push()
            dockerImage.push(buildTag)
            dockerImage.push("prd-latest")
          }
        }
      }
    }

  }

  post {
    always {
      sh "docker rmi " + dockerImage.id
    }
  }

}