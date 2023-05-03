# JUPYTER_OPTS="--no-browser"
JUPYTEROPTS=""
# DEFAULTNOTEBOOK="/notebooks/notebooks/overview.ipynb"


jupyter --paths

# Start Jupyter
# cmd="env PYTHONPATH=`pwd` {PYTHON:-/usr/bin/python3} -s /usr/bin/jupyter-notebook $JUPYTER_OPTS --notebook-dir=$notebookdir --NotebookApp.default_url=$DEFAULTNOTEBOOK"
# cmd="env PYTHONPATH=`pwd` jupyter notebook $JUPYTER_OPTS --notebook-dir=$notebookdir --NotebookApp.default_url=$DEFAULTNOTEBOOK"
# cmd="env PYTHONPATH=`pwd` jupyter notebook $JUPYTER_OPTS --NotebookApp.default_url=$DEFAULTNOTEBOOK"
cmd="env PYTHONPATH=`pwd` jupyter notebook $JUPYTER_OPTS"
echo -e "\n$cmd\n"
$cmd
