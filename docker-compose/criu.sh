#!/bin/bash
docker exec oai-amf date +%Y-%m-%d' '%H:%M:%S.%N | cut -b 1-26
docker checkpoint create oai-amf oai-amf-cp
docker start --checkpoint oai-amf-cp oai-amf
docker exec oai-amf date +%Y-%m-%d' '%H:%M:%S.%N | cut -b 1-26