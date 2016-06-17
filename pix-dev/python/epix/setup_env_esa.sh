setenv MON $PWD
#set DAQ="/home/epix/run_software"
set DAQ="/home/epix/devel/epix_software_trunk_devel"
if($#argv > 1) then
    set DAQ = $argv[1]
endif
pushd $DAQ
source setup_env_esa.csh
popd

setenv PYTHONPATH ${PYTHONPATH}:${BASE}/python/pylib

setenv DATADIR /home/epix/data

