#!/usr/bin/env python
import os
import base64
import utils



if __name__ == "__main__":
    # Test keys
    home_dir = os.path.expanduser("~")
    username = b"test_user"
    private_path = os.path.join(home_dir, ".ssh", "id_rsa")
    public_path = os.path.join(home_dir, ".ssh", "id_rsa.pub")
    private_key = utils.load_private_key(private_path)
    public_key = utils.load_public_key(public_path)


