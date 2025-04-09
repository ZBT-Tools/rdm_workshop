# Repository for the internal RDM Workshop at ZBT
To fully use this repository it is advised to clone it via git
(create a local version of this repository on your laptop).
Therefore you need to install git: https://gitforwindows.org/
With the installed Git Bash command-line interface tool navigate into the folder, 
where you want to clone (copy) this repository into via
> cd 'D:\path\to\your\project' (for Windows)'

> git clone https://github.com/ZBT-Tools/rdm_workshop.git

Alternatively, you can also direct download the complete repository 
(however then not integrated into git version control):

<img src="https://github.com/user-attachments/assets/c4f9b990-c9d2-4389-b15c-9405bdfb3c9f" alt="drawing" width="400"/>

The presentations are saved under the folder `presentations`

The required python packages for the examples exercises are located in the `requirements.txt` file.
Installation of all packages can be performed (with an activated python environment, e.g. system-wide, conda or venv)
from a terminal in the's working directory:
> pip install -r requirements.txt

The example exercises are located in two separate jupyter notebooks:
1. for the data upload to MongoDB: `mongodb_upload.ipynb`
2. for processing the data from MongoDB: `data_processing.ipynb`
