for file in $(ls data/*.json); do  \
  java -jar bin/vespa-http-client-jar-with-dependencies.jar \
    --verbose --file $file --endpoint http://localhost:8080; 
done
