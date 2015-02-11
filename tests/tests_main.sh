#!/bin/bash

################################################################################
# Copyright 2013 Ricardo Tubio-Pardavila (rtpardavila@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
# Author: xabicrespog[at]gmail.com
# Description: runs all the different tests for the protocol using twisted 
# tools (trial)
################################################################################

# ### Main variables and parameters
script_path="$( cd "$( dirname "$0" )" && pwd )"
project_path="$script_path/.."
webservices_dir="$project_path/WebServices"
webservices_manage_py="$webservices_dir/manage.py"
unittests="$script_path/unittests"


# ### Examples of HOW TO call this script
usage()
{

    echo "Usage: $0 [-c] #Cleans Django database and create empty tables"
    echo "Usage: $0 [-l] #Run tests for the loging module"
    echo "Usage: $0 [-p] #Run tests for the protocol" 

    1>&2;
    exit 1; 

}

if [ $# -lt 1 ] ; then
    usage
    exit 0
fi

while getopts ":clp" opt; do
    case $opt in
        c)
            echo 'Cleaning Django DB...'
            python $webservices_manage_py flush --noinput
            echo 'DONE'
            exit 1
            ;;
        l)
            echo 'Running tests for the login module...'
            python "$unittests/test_login_populateDB.py"
            trial "$unittests/test_login_singleClient.py"
            trial "$unittests/test_login_multipleClients.py"
            echo 'DONE'
            exit 1
            ;;
        p)
            echo 'Running tests for protocol...'
            python "$unittests/test_startRemote_populateDB.py"
            trial "$unittests/test_startRemote.py"
            echo 'DONE'
            ;;

        *)
            usage
            ;;
    esac

    shift $((OPTIND-1))

done