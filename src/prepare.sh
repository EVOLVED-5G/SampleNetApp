cp capif_registration_template.json capif_registration.json

jq -r .capif_host=\"$CAPIF_HOSTNAME\" capif_registration.json >> tmp.json && mv tmp.json capif_registration.json
jq -r .folder_to_store_certificates=\"$PATH_TO_CERTS\" capif_registration.json >> tmp.json && mv tmp.json capif_registration.json
jq -r .capif_http_port=\"$CAPIF_PORT\" capif_registration.json >> tmp.json && mv tmp.json capif_registration.json
jq -r .capif_https_port=\"$CAPIF_PORT_HTTPS\" capif_registration.json >> tmp.json && mv tmp.json capif_registration.json
jq -r .capif_callback_url=\"http://$CALLBACK_ADDRESS\" capif_registration.json >> tmp.json && mv tmp.json capif_registration.json
jq -r .csr_common_name=\""zorte"$(date +%s)\" capif_registration.json >> tmp.json && mv tmp.json capif_registration.json
jq -r .capif_netapp_username=\""zorte"$(date +%s)\" capif_registration.json >> tmp.json && mv tmp.json capif_registration.json

evolved5g register-and-onboard-to-capif --config_file_full_path="/zortenet_netapp/capif_registration.json" --environment="$ENVIRONMENT_MODE"

python3  /zortenet_netapp/api.py

