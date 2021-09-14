docker run -it --rm -v "$(pwd)":/opt/maven -w /opt/maven maven:3.8-openjdk-11 mvn clean package

curl --header Content-Type:application/zip --data-binary @target/application.zip \
  localhost:19071/application/v2/tenant/default/prepareandactivate | jq '.'
