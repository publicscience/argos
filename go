#!/bin/bash
trap : SIGTERM SIGINT

echo -e "\n\n\n\n\n"
echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo -e "$(tput setaf 6)Summoning the $(tput setaf 3)Argos$(tput setaf 6) environment with PID $(tput setaf 1)$$$(tput sgr0)"
echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo -e "\n\n\n\n\n"


# Run everything in the background,
# but remember their process IDs.

redis-server &
REDIS_PID=$!

rabbitmq-server &
RABMQ_PID=$!

cd ner
java -mx1000m -cp stanford-ner.jar edu.stanford.nlp.ie.NERServer -loadClassifier classifiers/english.conll.4class.distsim.crf.ser.gz -port 8080 -outputFormat inlineXML &
NERSV_PID=$!
cd ..

cd jena/fuseki
./fuseki-server --loc=${HOME}/knodb /knowledge &
KNOSV_PID=$!
cd ../..

source dev-env/bin/activate
celery worker --loglevel=DEBUG --app=argos.tasks.celery
WORKR_PID=$!

wait

if [[ $? -gt 128 ]]
then

    echo -e "\n\n\n\n\n"
    echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo -e "$(tput setaf 6)Exiting the $(tput setaf 3)Argos$(tput setaf 6) environment.$(tput sgr0)"
    echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo -e "\n\n\n\n\n"

    kill $REDIS_PID
    kill $RABMQ_PID
    kill $NERSV_PID
    kill $KNOSV_PID
    kill $WORKR_PID
fi
