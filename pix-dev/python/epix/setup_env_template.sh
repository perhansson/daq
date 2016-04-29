setenv MON $PWD
if ( ! ($?BASE) ) then
    if($#argv > 0) then
	echo "Setting up DAQ directory $argv[1]"
	pushd $argv[1]
	source setup_env_template.csh
	popd
    else
	echo "Error: Please supply a DAQ directory as first argument or setup up before running this script."
	exit 0
    endif
else
    echo "DAQ directory is ${BASE}"    
endif

