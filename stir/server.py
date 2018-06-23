#!/usr/bin/env python

import base64
import os
import sys
import time
import logging

logger = logging.getLogger("stir")

# python import foo
local_dir = os.path.realpath(
    os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, local_dir)

import stir.utils as utils
from stir.models import Org, SshKey, User, UserOrg

if __name__ == "__main__":
    # Test keys
    home_dir = os.path.expanduser("~")
    username = b"test_user"
    private_path = os.path.join(home_dir, ".ssh", "id_rsa")
    public_path = os.path.join(home_dir, ".ssh", "id_rsa.pub")
    private_key = utils.load_private_key(private_path)
    public_key = utils.load_public_key(public_path)
    sig_time = time.time()
    signature = utils.sign_message(str(sig_time), private_key)
    utils.verify_message(str(sig_time), signature, public_key)



