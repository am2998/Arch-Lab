FROM archlinux:latest

# System update and install prerequisites
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm base-devel git sudo go \
    xorg-xinit tigervnc xfce4 xfce4-terminal thunar mousepad ristretto

# Create user and allow passwordless sudo
RUN useradd -m -G wheel docker && echo "docker:docker" | chpasswd && \
    echo '%wheel ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/99-wheel-nopasswd && \
    chmod 0440 /etc/sudoers.d/99-wheel-nopasswd

USER docker
WORKDIR /home/docker

# Install yay as docker user
RUN git clone https://aur.archlinux.org/yay.git && \
    cd yay && \
    makepkg -si --noconfirm

# Use yay to install xrdp
RUN yay -S --noconfirm xrdp

USER root

# Configure xfce4 session for RDP
RUN echo "xfce4-session" > /home/docker/.xsession && \
    chown docker:docker /home/docker/.xsession && \
    systemctl enable xrdp && \
    systemctl enable xrdp-sesman

# Expose RDP port
EXPOSE 3389

# Launch xrdp services
CMD ["/bin/bash", "-c", "/usr/bin/xrdp-sesman & exec /usr/bin/xrdp -nodaemon"]