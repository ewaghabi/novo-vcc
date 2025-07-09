import sys
from streamlit.web import cli as stcli

# Arquivo de entrada que inicializa a aplicação Streamlit

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app/ui/chat.py"]  # prepara chamada ao Streamlit
    sys.exit(stcli.main())
