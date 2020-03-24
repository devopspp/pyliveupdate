"""Runs protoc with the gRPC plugin to generate messages and gRPC stubs."""

from grpc_tools import protoc

protoc.main((
    '',
    '-I.',
    '--python_out=.',
    '--grpc_python_out=.',
    'updatestub.proto',
))

protoc.main((
    '',
    '-I.',
    '--python_out=.',
    '--grpc_python_out=.',
    'updatestubproxy.proto',
))