from utils.opensearch import OpenSearchService
from utils.embedding import get_embedding_bedrock
import boto3

from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.utils.export import generate_multimodal_pages
from docling.utils.utils import create_hash
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)

text_max_length = 300

def conver_file(file_path):
    IMAGE_RESOLUTION_SCALE = 2.0
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_page_images = True

    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=10, device=AcceleratorDevice.AUTO
    )

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    conv_res = doc_converter.convert(file_path)

    rows = []
    for (
        content_text,
        content_md,
        content_dt,
        page_cells,
        page_segments,
        page,
    ) in generate_multimodal_pages(conv_res):

        rows.append(
            {
                "content_md": content_md,
                "page_num": page.page_no
            }
        )

    return rows

def load_data_to_opensearch(opensearch_client,index,row,embedding_model='cohere.embed-multilingual-v3'):
    content = row["content_md"]
    sentences = content.split('\n')
    texts = []
    metadatas = []
    embeddings = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 0:
            metadata = {}
            metadata['sentence'] = sentence[:text_max_length] if len(sentence) > text_max_length else sentence
            metadata['source'] = file.split('/')[-1]
            metadata['page_num'] = row["page_num"]
            metadatas.append(metadata)
            texts.append(content)
            sentence_embedding = get_embedding_bedrock(embedding_model,sentence)
            embeddings.append(sentence_embedding)

        opensearch_client.add_documents(
            index,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )


