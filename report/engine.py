import enum
import io


class OutputFormat(enum.Enum):
    LATEX = 1


def generate_report(input_data: dict, output_stream: io.BufferedWriter, components: list, format: OutputFormat) -> None:
    pass