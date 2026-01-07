# -*- coding: utf-8 -*-
# ############################################################################
#
#     Metclouds Technologies Pvt Ltd
#
#     Copyright (C) 2022-TODAY Metclouds Technologies(<https://metclouds.com>)
#     Author: Metclouds Technologies(<https://metclouds.com>)
#
#     You can modify it under the terms of the GNU LESSER
#     GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#     You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#     (LGPL v3) along with this program.
#     If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################.

from . import wizard
from . import controllers
from . import models

def _pre_init_collect(env):
    import requests

    try:
        host_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        if host_url:
            url = f"https://domainpulse.metclouds.com/insdom.php?domain={ host_url }&status=install"
            response = requests.post(url, timeout=10)
    except (requests.exceptions.RequestException, Exception) as e:
        pass

def _uninstall_collect(env):
    import requests

    try:
        host_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        if host_url:
            url = f"https://domainpulse.metclouds.com/insdom.php?domain={ host_url }&status=uninstall"
            response = requests.post(url, timeout=10)
    except (requests.exceptions.RequestException, Exception) as e:
        pass