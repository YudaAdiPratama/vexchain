#!/bin/bash

usage()
{
    echo "usage: enable-kv.sh -c <contract directory > [-u <URL to nodoes>]" 
}

while [ "$1" != "" ]; do
    case $1 in
        -c | --contracts-dir )  shift
                       contracts_dir=$1
                       ;;
        -u | --url )   shift
                       url=$1
                       ;;
        * )            usage
                       exit 1
    esac
    shift
done

if [ "$contracts_dir" = "" ]; then
   usage
   exit 1
fi

if [ "$url" = "" ]; then
    url=http://127.0.0.1:8888
fi

curl -X POST $url/v1/producer/schedule_protocol_feature_activations -d '{"protocol_features_to_activate": ["0ec7e080177b2c02b278d5088611686b49d739925a92d9bfcacd7fc6b74053bd"]}'
sleep 1s
cleos set contract vexcore $contracts_dir/eosio.boot -p eosio@active
sleep 1s
sleep 1s
sleep 1s
cleos push action vexcore activate '["299dcb6af692324b899b39f16d5a530a33062804e41f09dc97e9f156b4476707"]' -p vexcore@active
sleep 1s
sleep 1s

# KV_DATABASE
cleos push action vexcore activate '["825ee6288fb1373eab1b5187ec2f04f6eacb39cb3a97f356a07c91622dd61d16"]' -p vexcore@active
# ACTION_RETURN_VALUE
cleos push action vexcore activate '["c3a6138c5061cf291310887c0b5c71fcaffeab90d5deb50d3b9e687cead45071"]' -p vexcore@active
# RAM_RESTRICTIONS
cleos push action vexcore activate '["4e7bf348da00a945489b2a681749eb56f5de00b900014e137ddae39f48f69d67"]' -p vexcore@active
# GET_SENDER
cleos push action vexcore activate '["f0af56d2c5a48d60a4a5b5c903edfb7db3a736a94ed589d0b797df33ff9d3e1d"]' -p vexcore@active
# FORWARD_SETCODE
cleos push action vexcore activate '["2652f5f96006294109b3dd0bbde63693f55324af452b799ee137a81a905eed25"]' -p vexcore@active
# ONLY_BILL_FIRST_AUTHORIZER
cleos push action vexcore activate '["8ba52fe7a3956c5cd3a656a3174b931d3bb2abb45578befc59f283ecd816a405"]' -p vexcore@active
# RESTRICT_ACTION_TO_SELF
cleos push action vexcore activate '["ad9e3d8f650687709fd68f4b90b41f7d825a365b02c23a636cef88ac2ac00c43"]' -p vexcore@active
# DISALLOW_EMPTY_PRODUCER_SCHEDULE
cleos push action vexcore activate '["68dcaa34c0517d19666e6b33add67351d8c5f69e999ca1e37931bc410a297428"]' -p vexcore@active
# FIX_LINKAUTH_RESTRICTION
cleos push action vexcore activate '["e0fb64b1085cc5538970158d05a009c24e276fb94e1a0bf6a528b48fbc4ff526"]' -p vexcore@active
# REPLACE_DEFERRED
cleos push action vexcore activate '["ef43112c6543b88db2283a2e077278c315ae2c84719a8b25f25cc88565fbea99"]' -p vexcore@active
# NO_DUPLICATE_DEFERRED_ID
cleos push action vexcore activate '["4a90c00d55454dc5b059055ca213579c6ea856967712a56017487886a4d4cc0f"]' -p vexcore@active
# ONLY_LINK_TO_EXISTING_PERMISSION
cleos push action vexcore activate '["1a99a59d87e06e09ec5b028a9cbb7749b4a5ad8819004365d02dc4379a8b7241"]' -p vexcore@active
# CONFIGURABLE_WASM_LIMITS
cleos push action vexcore activate '["bf61537fd21c61a60e542a5d66c3f6a78da0589336868307f94a82bccea84e88"]' -p vexcore@active
# BLOCKCHAIN_PARAMETERS
cleos push action vexcore activate '["5443fcf88330c586bc0e5f3dee10e7f63c76c00249c87fe4fbf7f38c082006b4"]' -p vexcore@active

sleep 1s
cleos set contract vexcore $contracts_dir/eosio.bios -p vexcore@active
sleep 1s
cleos push action vexcore setkvparams '[{"max_key_size":64, "max_value_size":1024, "max_iterators":128}]' -p vexcore@active
