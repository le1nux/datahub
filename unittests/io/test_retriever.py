from data_hub.io.retriever import RetrieverFactory, HTTPRetrieverImpl, Retriever, RetrievalJob
from data_hub.io.storage_connectors import StorageConnectorFactory, StorageConnector
from data_hub.io.resources import StreamedResource
import pytest
import hashlib


class TestBaseRetriever:

    @pytest.fixture
    @pytest.mark.usefixtures("tmp_folder_path")
    def storage_connector(self, tmp_folder_path: str) -> StorageConnector:
        return StorageConnectorFactory.get_file_storage_connector(tmp_folder_path)

    @staticmethod
    def get_md5(resource: StreamedResource):
        md5 = hashlib.md5()
        for chunk in iter(lambda: resource.read(1024 * 1024), b''):
            md5.update(chunk)
        return md5.hexdigest()


class TestRetrieverFactory(TestBaseRetriever):

    def test_get_http_retriever(self, storage_connector: StorageConnector):
        http_retriever = RetrieverFactory.get_http_retriever(storage_connector)
        assert isinstance(http_retriever.retriever_impl, HTTPRetrieverImpl)


class TestRetriever(TestBaseRetriever):
    @pytest.fixture
    def http_retrieval_job(self) -> RetrievalJob:
        return RetrievalJob(identifier="my_resouce",
                            source="http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz",
                            md5_sum="ec29112dd5afa0611ce80d1b7f02629c")

    @pytest.fixture
    def http_retriever(self, storage_connector: StorageConnector):
        return RetrieverFactory.get_http_retriever(storage_connector)

    @pytest.fixture
    def http_retriever_impl(self, storage_connector: StorageConnector):
        return HTTPRetrieverImpl(storage_connector)

    def test_http_retriever_retrieve(self, http_retriever: Retriever, http_retrieval_job: RetrievalJob):
        http_retriever.retrieve([http_retrieval_job])
        storage_connector = http_retriever.retriever_impl.storage_connector
        resource = storage_connector.get_resource(http_retrieval_job.identifier)
        assert TestBaseRetriever.get_md5(resource) == http_retrieval_job.md5_sum

    def test_http_retriever_impl_download_file(self, http_retriever_impl: HTTPRetrieverImpl, http_retrieval_job: RetrievalJob, tmp_folder_path: str):
        file_path = http_retriever_impl._download_file(url=http_retrieval_job.source,
                                                       dest_folder=tmp_folder_path,
                                                       md5=http_retrieval_job.md5_sum)
        with open(file_path, "rb") as fd:
            md5_sum = TestBaseRetriever.get_md5(fd)
        return md5_sum == http_retrieval_job.md5_sum