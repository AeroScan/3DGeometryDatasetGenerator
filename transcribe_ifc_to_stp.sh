while getopts i: flag
do
	case "${flag}" in
		i) input_dir=${OPTARG};;
	esac
done

find ${input_dir} -name "*.ifc" | while read -r FILE; do
	/opt/IfcConvert $FILE $FILE.stp
done
