# Install git, pip, clojure.
sudo apt-get update
sudo apt-get install git python-pip leiningen

# Download project source code
git clone https://github.com/jpvelez/cubisima.git
cd cubisima
sudo pip install -r requirements.txt

# Install drake
cd ..
git clone https://github.com/Factual/drake.git
cd drake
lein uberjar

# Configure drake shell command
echo '#!/bin/bash
java -cp $(dirname $0)/drake.jar drake.core "$@"' > drake
sudo mv drake /usr/bin/
sudo chmod 755 /usr/bin/drake
sudo mv target/drake.jar /usr/bin/