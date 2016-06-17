setenv MON $PWD
set DAQ="/projects/epix_trunk/software"
pushd $DAQ
source setup_env_nlcta.csh
popd

setenv PYTHONPATH ${PYTHONPATH}:${BASE}/python/pylib

setenv DATADIR /data

