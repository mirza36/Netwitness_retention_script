#!/bin/bash
# get-all-systems.sh v11.2 
#
BUPATH="/var/netwitness/nw-backup"
#----------------------------- DO NOT Edit below this line ------------------------------------
#
# Creates file with list of all minions known to salt for use with the nw-backup11.sh script.
# Appliance Type,Hostname,IP_Address,Minion_ID,Serial_Number,NW_Version
# Script MUST be run from the NW Admin {node-zero} Server
#
# If differences are found from previous run (systems added/deleted) will generate new-systems and/or old-systems files.
#
# Set Output Colors
RED=`tput setaf 1`
GRB=`tput setaf 2; tput bold`
YLW=`tput setaf 3`
BLB=`tput setaf 4; tput bold`
BLD=`tput bold`
RST=`tput sgr0`
#
# ----------------------- DEFINE FUNCTIONS -----------------------
#
#-------------- LOG FUNCTIONS ------------------
#
# Write status messages to log file & screen
function writeLog() {
    echo "$(date '+%Y-%m-%d %H:%M:%S %z') | $$ | $1" | sed -e "s/\x1B\[[(0-9;]*[JKBmsu]//g" -e "s/\x1B\x28B//g" >> ${LOG}
    echo "$1"
}
#
#---------- PRE-RUN VERIFICATION FUNCTIONS -------------
#
# Verify environment is configured to successfully run the script
function check-paths() {
# Verify BUPATH is not empty
if [ -z "${BUPATH}" ];then
    echo ""
    echo "${RED}ERROR: ${YLW}Backup path has not been set!${RST}" 
    echo "Please edit the ${0} file and set the value of BUPATH on line 4 to reflect"
    echo "the location the backup files to be stored and then run this script again"
    echo ""
    echo "Exiting on critical error..."
    exit 1
else
    echo "BUPATH set...          [${GRB} OK ${RST}]            Backup path has been set to ${GRB}${BUPATH}${RST}"
fi
# Verify the BUPATH target exists and is a directory, if not create it.
if [ ! -d "${BUPATH}" ];then
    mkdir -p ${BUPATH}
    if [[ $? -eq 0 ]];then
        echo "BUPATH Directory...   [${GRB} OK ${RST}]            Created Backup Directory: ${GRB}${BUPATH}${RST}"
    else
        echo ""
        echo "Failed to Create directory ${GRB}${BUPATH}${RST}, check BUPATH variable and permissions for ${GRB}${RUNUSER}${RST} for that path."
        echo ""
        echo "Exiting on critical error..."
        exit 1
    fi
else
    echo "BUPATH exists...       [${GRB} OK ${RST}]"
fi
}
#
# Verify script is running on the NW server (Node0) server, check for existing output file.
function check-targets() {
# Check to see if target host is an NW Server (Salt-Master running on port 4505)
if ! (exec 3<>/dev/tcp/127.0.0.1/4505) 2> /dev/null;then
    writeLog ""
    writeLog "${RED}Error: ${YLW}Host is not responding on salt-master port 4505...${RST}"
    writeLog "Either $(hostname) is not a NW Node0 Server, or the salt-master.service is not running."
    writeLog ""
    writeLog "Exiting on critical error..."
    exit 1
else
    writeLog "salt-master service... [${GRB} OK ${RST}]"
fi
# check if mongo is running
 if ! (exec 3<>/dev/tcp/127.0.0.1/27017) 2> /dev/null;then
    writeLog ""
    writeLog "${RED}Error: ${YLW}Host is not responding on mongo service port 27017...${RST}"
    writeLog "The mongo.service is not running or is dead."
    writeLog ""
    writeLog "Exiting on critical error..."
    exit 1
else
    writeLog "mongo service...       [${GRB} OK ${RST}]"
fi
# Check for existing new-systems/old-systems files, and if already exist, archive them with timestamp?
if [ -s "${NS_FILE}" ];then
    writeLog ""
    writeLog "The file ${GRB}${NS_FILE}${RST} already exists, archiving to ${NS_FILE}_${TIMESTAMP}..."
    mv ${NS_FILE} ${NS_FILE}_${TIMESTAMP} && echo ""
fi
if [ -s "${OS_FILE}" ];then
    writeLog ""
    writeLog "The file ${GRB}${OS_FILE}${RST} already exists, archiving to ${OS_FILE}_${TIMESTAMP}..."
    mv ${OS_FILE} ${OS_FILE}_${TIMESTAMP} && echo ""
fi
# If all-systems file already exists, overwrite?
if [ -s "${OUT_FILE}" ];then
    writeLog ""
    writeLog "${YLW}Warning: ${RST}The file ${GRB}${OUT_FILE}${RST} already exists!!!!!"
    read -t 30 -p "Do you want to archive or overwrite existing file? (defaults to Archive in 30 seconds) (${GRB}a/o${RST})? " choice
    if [ $? -eq 0 ];then
        writeLog ""
        case "${choice}" in
            a|A ) mv ${OUT_FILE} ${OUT_FILE}_${TIMESTAMP} && touch ${OUT_FILE} && writeLog "Archiving all-systems file to all-systems_${TIMESTAMP}..." && echo "";;
            o|O ) rm -f ${OUT_FILE} && touch ${OUT_FILE} && writeLog "Overwriting all-systems file..." && echo "";;
            *   ) writeLog -e "${RED}Error: ${YLW}Invalid input.${RST}\n\nExiting on Critical Error\n" && exit 1;;
        esac
    else
         mv ${OUT_FILE} ${OUT_FILE}_${TIMESTAMP} && touch ${OUT_FILE} && writeLog "Archiving all-systems file to all-systems_${TIMESTAMP}..." && echo ""
    fi
else
    writeLog "No existing all-systems file, creating..."
    touch ${OUT_FILE} 
    echo ""
fi

}
#
#-------------- CORE-RUN FUNCTIONS -----------------
#
function get-host-info() {
# Get "deploy_admin" password
DEPLOY_PW=$(security-cli-client --get-config-prop --prop-hierarchy nw.security-client --prop-name platform.deployment.password --quiet)
# Get Host information from Orchestration Database
writeLog "Gathering Host Service info from Orchestration MongoDB..."
mongoexport --type=csv -d orchestration-server -c host -u deploy_admin -p ${DEPLOY_PW} --authenticationDatabase=admin -f _id,installedServices,version --quiet | sed -e 's/[^a-zA-Z0-9\.,[:space:]-]//g' | awk -F, '{print $1","$2","$NF}' | sed -e 's/rawVersion//g' > ${SVC_INFO}
# Get Host System Information from Salt Grains
writeLog "Gathering Host System info from Salt Grains..."
salt '*' grains.item nodename ipv4 id serialnumber --out=newline_values_only 2>/dev/null | tr -d "{}[]\ \'" | sed -e 's/:/,/g' -e 's/127.0.0.1,//' -e '/installedServices/d' -e '/Miniondidnotreturn/d' | awk -F, '{print $2","$6","$8","$4}' > "${SYS_INFO}"
}
#
function gen-all-systems() {
# Generate all-systems file from HOST_INFO and salt grains
writeLog "Generating ${GRB}${OUT_FILE}${RST}"
echo -n "Please standby..."
while IFS=',' read -r HSTNM HSTIP HSTID HSTSN;do
    echo -n "."
    # Find Device Type
    DEVTYP=$(grep "${HSTID}" ${SVC_INFO} | awk -F, '{print $2}' | xargs)
    # Find Host Version
    HSTVER=$(grep ${HSTID} ${SVC_INFO} | awk -F, '{print $3}' | xargs)
    echo -n "."
    # Append Data to AS_TMP
    echo "${DEVTYP},${HSTNM},${HSTIP},${HSTID},${HSTSN},${HSTVER}" >> "${AS_TMP}"
done < ${SYS_INFO}
echo ""
# Sort output to OUT_FILE
sort -t, -k1 -o ${OUT_FILE} ${AS_TMP}
}
#
function check-new-old() {
# Check for new systems (difference in old file and new file)
comm -23 "${OUT_FILE}" "${MASTER_OUT_FILE}" > "${NS_TMP}"
comm -13 "${OUT_FILE}" "${MASTER_OUT_FILE}" > "${OS_TMP}"
if [ -s "${NS_TMP}" ];then
    writeLog "New systems found, generating ${GRB}new-systems${RST} file."
    cat ${NS_TMP} > ${NS_FILE}
else
    writeLog "No new systems detected, new-systems file will not generated"
fi
if [ -s "${OS_TMP}" ];then
    writeLog "Found missing (old) systems, generating ${GRB}old-systems${RST} file."
    cat ${OS_TMP} > ${OS_FILE}
else
    writeLog "No missing systems detected, old-systems file will not generated"
fi
}
#
#--------------- POST-RUN FUNCTIONS --------------------

# verify content of the all-systems file
function check-output(){
    if [[ -s "${OUT_FILE}" ]]; then
        while IFS=',' read -r f1 f2 f3 f4 f5 f6
        do
            if [[ -z "${f1// }" ]] || [[ -z "${f2// }" ]] || [[ -z "${f3// }" ]] || [[ -z "${f4// }" ]] || [[ -z "${f5// }" ]] || [[ -z "${f6// }" ]]; then
                echo "${RED}ERROR: ${YLW}$f1,$f2,$f3,$f4,$f5,f6 line in ${OUT_FILE} has invalid entries or empty spaces.${RST}" >> "${ERRLOG}"
                ((ERRCNT++))
            fi
        done < "$OUT_FILE"
    return 0
    else
        writeLog "${RED}ERROR: ${YLW}${OUT_FILE} file is either missing or empty. Please verify."
        writeLog "${YLW}Ensure ${OUT_FILE} and ${MASTER_OUT_FILE} have same entries before running nw-backup script.${RST}"
        writeLog ""
    if [[ -s "${MASTER_OUT_FILE}" ]];then
            writeLog "Restoring all-systems file from previous all-systems-master-copy"
            cp ${MASTER_OUT_FILE} ${OUT_FILE}
    else
        writeLog "No existing ${MASTER_OUT_FILE} to restore."
    fi
    return 1
    fi
}
#
function clean-up() {
# Clean up the temp files.
    rm -f "${SVC_INFO}" "${SYS_INFO}" "${AS_TMP}" "${NS_TMP}" "${OS_TMP}" &> /dev/null
}
#
function screen-dump() {
# Dump the output file to the terminal
    writeLog ""
    writeLog "Below is the contents of the ${GRB}${OUT_FILE}${RST}"
    writeLog "Please verify information is correct and complete before using with the backup/restore scripts"
    writeLog ""
    cat ${OUT_FILE} | tee -a ${LOG}
    if [ -s "${NS_FILE}" ];then
        writeLog ""
        writeLog "${YLW}${BLD}NEW SYSTEMS${RST}"
        writeLog "Below is the contents of the ${GRB}${NS_FILE}${RST} file."
        writeLog "Please verify information is correct and complete before using with the any scripts"
        writeLog ""
        cat ${NS_FILE} | tee -a ${LOG}
    fi
    if [ -s "${OS_FILE}" ];then
        writeLog ""
        writeLog "${RED}${BLD}OLD or MISSING SYSTEMS${RST}"
        writeLog "Below is the contents of the ${GRB}${OS_FILE}${RST} file."
        writeLog "Please verify these systems have actually been removed from the environment, check salt-minion service on device and re-run this script"
        writeLog ""
        cat ${OS_FILE} | tee -a ${LOG}
    fi
}
#---------------------- END OF FUNCTION DEFINITIONS ------------------------
#
#----------------- Main Program Start -----------------------
#
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%d-%H%M)
echo ""
echo "Starting execution of ${GRB}get-all-systems.sh${RST}"
echo ""
# Check paths for all output
check-paths
#
# Set logging environment
LOG=${BUPATH}/rsa-get-all-systems11-${TODAY}.log
ERRLOG=`mktemp`
#
# Initialize variables
OUT_FILE=${BUPATH}/all-systems
MASTER_OUT_FILE=${BUPATH}/all-systems-master-copy
NS_FILE=${BUPATH}/new-systems
OS_FILE=${BUPATH}/old-systems
RUNUSER=$(whoami)
ERRCNT=0
# Make temp files
SVC_INFO=`mktemp`
SYS_INFO=`mktemp`
AS_TMP=`mktemp`
NS_TMP=`mktemp`
OS_TMP=`mktemp`
# Check Target Server Up and if all-systems already exists
check-targets
# Get Host info from MongoDB and List of Minions from salt
get-host-info
# Generate the "all-systems" file
gen-all-systems
# Verify output file and list any hosts with missing data in ERRLOG
check-output
if [ $? -eq 0 ];then
    # Check of new or old(missing) systems
    if [ -s "${MASTER_OUT_FILE}" ];then
        check-new-old
    fi
    # Create or Update the master copy of the all-systems file if all-systems file exists
    writeLog "Creating master copy of all-systems file as: ${MASTER_OUT_FILE}"
    cp ${OUT_FILE} ${MASTER_OUT_FILE}
    # Dump files to screen for verification
    screen-dump
    # Cleanup temp files
    clean-up
    if [[ ${ERRCNT} -eq 0 ]];then
        writeLog ""
        writeLog "${GRB}get-all-systems ${RST}completed with no errors."
        exit 0
    else
        writeLog ""
        writeLog "${YLW}Warning:${RST} Generation of {GRB}all-systems${RST} completed with ${RED}${ERRCNT}${RST} errors, please review log file @ ${GRB}${LOG}${RST}."
        cat ${ERRLOG} >> ${LOG}
        rm -f "${ERRLOG}"
        exit 1
    fi
else
    writeLog "Failed to generate ${OUT_FILE}, Exiting on critical error..."
    writeLog ""
    # Cleanup temp files
    clean-up
    exit 1
fi
