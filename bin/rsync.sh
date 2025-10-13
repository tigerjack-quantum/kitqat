#!/bin/bash - 
#===============================================================================
#
#          FILE: rsync.sh
# 
#         USAGE: ./rsync.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: YOUR NAME (), 
#  ORGANIZATION: 
#       CREATED: 30/04/2025 14:31
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
PROJECT=qat-utils
PROJECT_ROOT=/mnt/internal/LinuxData/vc/quantum
SERVER=$1

rsync -avz --info=progress2 \
  --filter="merge $PROJECT_ROOT/$PROJECT/rsync_filter.txt" \
  "$PROJECT_ROOT/$PROJECT" "$SERVER":vc/

