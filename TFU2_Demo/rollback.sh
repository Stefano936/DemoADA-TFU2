#!/bin/bash
echo "Revirtiendo a versión estable..."
docker-compose down
docker-compose -f docker-compose.rollback.yaml up -d
