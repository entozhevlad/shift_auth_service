FROM python:3.12-bookworm

RUN apt update && export DEBIAN_FRONTEND=noninteractive \
    && apt install -y build-essential python3-dev \
    && apt install -y manpages-dev vim nano curl wget zsh locales \
    && apt autoremove -y
ENV TERM xterm
ENV SHELL /bin/zsh
RUN locale-gen en_US.UTF-8 && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && /usr/sbin/locale-gen
RUN python3 -m pip install --upgrade setuptools pip
RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true
RUN git clone https://github.com/romkatv/powerlevel10k.git ~/.oh-my-zsh/custom/themes/powerlevel10k

COPY post-start.sh /root/
COPY .zshrc /root/
# Настройки темы https://github.com/romkatv/powerlevel10k
COPY .p10k.zsh /root/
