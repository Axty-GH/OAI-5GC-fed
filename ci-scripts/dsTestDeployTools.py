#/*
# * Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
# * contributor license agreements.  See the NOTICE file distributed with
# * this work for additional information regarding copyright ownership.
# * The OpenAirInterface Software Alliance licenses this file to You under
# * the OAI Public License, Version 1.1  (the "License"); you may not use this file
# * except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *       http://www.openairinterface.org/?page_id=698
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# *-------------------------------------------------------------------------------
# * For more information about the OpenAirInterface (OAI) Software Alliance:
# *       contact@openairinterface.org
# */
#---------------------------------------------------------------------

import os
import re
import sys
import subprocess
import time

CICD_PRIVATE_NETWORK_RANGE='192.168.28.0/26'
CICD_PUBLIC_NETWORK_RANGE='192.168.61.192/26'

CICD_MYSQL_PUBLIC_ADDR='192.168.61.194'
CICD_AMF_PUBLIC_ADDR='192.168.61.195'

class deployForDsTester():
    def __init__(self):
        self.action = 'None'
        self.tag = ''
        self.mySqlPassword = ''

    def createNetworks(self):
        # first check if already up?
        try:
            res = subprocess.check_output('docker network ls | egrep -c "cicd-oai-public-net|cicd-oai-private-net"', shell=True, universal_newlines=True)
            if int(str(res.strip())) > 0:
                self.removeNetworks()
        except:
            pass

        subprocess_run_w_echo('docker network create --attachable --subnet ' + CICD_PUBLIC_NETWORK_RANGE + ' --ip-range ' + CICD_PUBLIC_NETWORK_RANGE + ' cicd-oai-public-net')
        subprocess_run_w_echo('docker network create --attachable --subnet ' + CICD_PRIVATE_NETWORK_RANGE + ' --ip-range ' + CICD_PRIVATE_NETWORK_RANGE + ' cicd-oai-private-net')

    def removeNetworks(self):
        try:
            subprocess_run_w_echo('docker network rm cicd-oai-public-net cicd-oai-private-net')
        except:
            pass

    def deployMySqlServer(self):
        # first check if already up? If yes, remove everything.
        try:
            res = subprocess.check_output('docker ps -a | grep -c "cicd-mysql-svr"', shell=True, universal_newlines=True)
            if int(str(res.strip())) > 0:
                self.removeAllContainers()
        except:
            pass

        subprocess_run_w_echo('docker run --name cicd-mysql-svr --network cicd-oai-public-net --ip ' + CICD_MYSQL_PUBLIC_ADDR + ' -d -e MYSQL_ROOT_PASSWORD=secretPassword mysql/mysql-server:5.7')
        # TEMPORARY: TODO --> when repos public, use component strategy
        subprocess_run_w_echo('docker cp ci-scripts/temp/oai_db.sql cicd-mysql-svr:/home')
        subprocess_run_w_echo('sed -e "s@CICD_AMF_PUBLIC_ADDR@' + CICD_AMF_PUBLIC_ADDR + '@" ci-scripts/mysql-script.cmd > ci-scripts/mysql-complete.cmd')
        subprocess_run_w_echo('docker cp ci-scripts/mysql-complete.cmd cicd-mysql-svr:/home')
        # waiting for the service to be properly started
        time.sleep(5)
        doLoop = True
        while doLoop:
            try:
                res = subprocess.check_output('docker logs cicd-mysql-svr 2>&1', shell=True, universal_newlines=True)
                startMessageFound = re.search('Starting MySQL', str(res))
                if startMessageFound is not None:
                    doLoop = False
            except:
                time.sleep(2)
                pass
        time.sleep(2)
        subprocess_run_w_echo('docker exec -it cicd-mysql-svr /bin/bash -c "mysql -uroot -psecretPassword < /home/mysql-complete.cmd"')

    def removeAllContainers(self):
        try:
            subprocess_run_w_echo('docker rm -f cicd-mysql-svr')
        except:
            pass


def subprocess_run_w_echo(cmd):
    print(cmd)
    subprocess.run(cmd, shell=True)

def Usage():
    print('----------------------------------------------------------------------------------------------------------------------')
    print('dsTestDeployTools.py')
    print('   Deploy for DsTester in the pipeline.')
    print('----------------------------------------------------------------------------------------------------------------------')
    print('Usage: python3 dsTestDeployTools.py [options]')
    print('  --help  Show this help.')
    print('---------------------------------------------------------------------------------------------- Mandatory Options -----')
    print('  --action={CreateNetworks,RemoveNetworks,...}')
    print('-------------------------------------------------------------------------------------------------------- Options -----')
    print('  --tag=[Image Tag in registry]')
    print('------------------------------------------------------------------------------------------------- Actions Syntax -----')
    print('python3 dsTestDeployTools.py --action=CreateNetworks')
    print('python3 dsTestDeployTools.py --action=RemoveNetworks')
    print('python3 dsTestDeployTools.py --action=DeployMySqlServer')
    print('python3 dsTestDeployTools.py --action=RemoveAllContainers')

#--------------------------------------------------------------------------------------------------------
#
# Start of main
#
#--------------------------------------------------------------------------------------------------------

DFDT = deployForDsTester()

argvs = sys.argv
argc = len(argvs)

while len(argvs) > 1:
    myArgv = argvs.pop(1)
    if re.match('^\-\-help$', myArgv, re.IGNORECASE):
        Usage()
        sys.exit(0)
    elif re.match('^\-\-action=(.+)$', myArgv, re.IGNORECASE):
        matchReg = re.match('^\-\-action=(.+)$', myArgv, re.IGNORECASE)
        action = matchReg.group(1)
        if action != 'CreateNetworks' and \
           action != 'RemoveNetworks' and \
           action != 'DeployMySqlServer' and \
           action != 'RemoveAllContainers':
            print('Unsupported Action => ' + action)
            Usage()
            sys.exit(-1)
        DFDT.action = action
    elif re.match('^\-\-tag=(.+)$', myArgv, re.IGNORECASE):
        matchReg = re.match('^\-\-tag=(.+)$', myArgv, re.IGNORECASE)
        DFDT.tag = matchReg.group(1)

if DFDT.action == 'CreateNetworks':
    DFDT.createNetworks()
elif DFDT.action == 'RemoveNetworks':
    DFDT.removeNetworks()
elif DFDT.action == 'DeployMySqlServer':
    DFDT.deployMySqlServer()
elif DFDT.action == 'RemoveAllContainers':
    DFDT.removeAllContainers()

sys.exit(0)
