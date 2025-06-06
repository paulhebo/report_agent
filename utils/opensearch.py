from opensearchpy import OpenSearch, RequestsHttpConnection,AWSV4SignerAuth
import json
import uuid
import boto3
from typing import Any, Dict, Iterable, List, Optional, Tuple
from dotenv import load_dotenv
import os

IMPORT_OPENSEARCH_PY_ERROR = (
    "Could not import OpenSearch. Please install it with `pip install opensearch-py`."
)

class OpenSearchService:
    def __init__(self):
        """
        initialize OpenSearch services
        
        """

        load_dotenv(verbose=True)
        host = os.getenv('opensearch_host') 
        region = os.getenv('region')
        username = os.getenv('opensearch_username')
        password = os.getenv('opensearch_password')
        
        print('host:',host)
        print('username:',username)
        print('password:',password)

        if len(host) > 0 and len(region) > 0 and len(username) > 0 and len(password) >0:
            hosts = [{'host': host, 'port': 443}]
            http_auth = (username, password)
            self.client = OpenSearch(hosts=hosts,http_auth=http_auth,use_ssl = True)

        elif len(host) > 0 and len(region) > 0: 
            service = 'aoss'
            credentials = boto3.Session().get_credentials()

            awsauth = AWSV4SignerAuth(credentials, region, service)

            self.client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=300
            )
        else:
            self.client = None


    def _import_bulk(self) -> Any:
        """Import bulk if available, otherwise raise error."""
        try:
            from opensearchpy.helpers import bulk
        except ImportError:
            raise ImportError(IMPORT_OPENSEARCH_PY_ERROR)
        return bulk
    
    def _import_not_found_error(self) -> Any:
        """Import not found error if available, otherwise raise error."""
        try:
            from opensearchpy.exceptions import NotFoundError
        except ImportError:
            raise ImportError(IMPORT_OPENSEARCH_PY_ERROR)
        return NotFoundError
    
    def _bulk_ingest_embeddings(
        self,
        index_name: str,
        embeddings: List[List[float]],
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        vector_field: str = "vector_field",
        text_field: str = "text",
        mapping: Optional[Dict] = None,
        max_chunk_bytes: Optional[int] = 1 * 1024 * 1024
    ) -> List[str]:
        """Bulk Ingest Embeddings into given index."""
        if not mapping:
            mapping = dict()
    
        bulk = self._import_bulk()
        not_found_error = self._import_not_found_error()
        requests = []
        #return_ids = []
        mapping = mapping
    
        try:
            self.client.indices.get(index=index_name)
        except not_found_error:
            self.client.indices.create(index=index_name, body=mapping)
    
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else {}
            #_id = ids[i] if ids else str(uuid.uuid4())
            request = {}
            if len(embeddings) > 0 :
                request = {
                    "_op_type": "index",
                    "_index": index_name,
                    vector_field: embeddings[i],
                    text_field: text,
                    "metadata": metadata,
                }

    
            #request["_id"] = _id
            requests.append(request)
            #return_ids.append(_id)
        bulk(self.client, requests, max_chunk_bytes=max_chunk_bytes)
        #self.client.indices.refresh(index=index_name)
        #return return_ids

    def _default_text_mapping(
        self,
        dim: int,
        engine: str = "nmslib",
        space_type: str = "l2",
        ef_search: int = 512,
        ef_construction: int = 512,
        m: int = 16,
        vector_field: str = "vector_field"
    ) -> Dict:
        """For Approximate k-NN Search, this is the default mapping to create index."""
        return {
            "settings": {"index": {"knn": True, "knn.algo_param.ef_search": ef_search}},
            "mappings": {
                "properties": {
                    vector_field: {
                        "type": "knn_vector",
                        "dimension": dim,
                        "method": {
                            "name": "hnsw",
                            "space_type": space_type,
                            "engine": engine,
                            "parameters": {"ef_construction": ef_construction, "m": m},
                        },
                    }
                }
            },
        }

    def add_documents(
            self,
            index_name: str,
            texts: Iterable[str],
            embeddings: List[List[float]],
            metadatas: Optional[List[dict]] = None,
            ids: Optional[List[str]] = None,
            bulk_size: int = 10000000,
            **kwargs: Any,
        ) -> List[str]:
            text_field = kwargs.get("text_field", "text")
            dim = len(embeddings[0]) if len(embeddings) > 0 else 0
            engine = kwargs.get("engine", "nmslib")
            space_type = kwargs.get("space_type", "l2")
            ef_search = kwargs.get("ef_search", 512)
            ef_construction = kwargs.get("ef_construction", 512)
            m = kwargs.get("m", 16)
            vector_field = kwargs.get("vector_field", "vector_field")
            max_chunk_bytes = kwargs.get("max_chunk_bytes", 1 * 1024 * 1024)
    
            mapping = self._default_text_mapping(
                dim, engine, space_type, ef_search, ef_construction, m, vector_field
            )

            self._bulk_ingest_embeddings(
                index_name,
                embeddings,
                texts,
                metadatas=metadatas,
                ids=ids,
                vector_field=vector_field,
                text_field=text_field,
                mapping=mapping,
                max_chunk_bytes=max_chunk_bytes
            )
    
    def vector_search(self, vector: List[float], index_name: str = '', size: int = 20,vector_field: str = "vector_field") -> List[Dict[str, Any]]:
        """
        vector search
        
        Args:
            vector: Query vector
            size: Number of results returned
            
        Returns:
            List[Dict[str, Any]]: return results
        """

        query = {
                "size": size,
                "query": {"knn": {vector_field: {"vector": vector, "k": size}}},
            }
        
        try:
            if self.client is not None:
                results = self.client.search(
                    body=query,
                    index=index_name
                )
                return results['hits']['hits']
            else:
                return {}
        except Exception as e:
            print(f"Vector search failed: {str(e)}")
            return []
