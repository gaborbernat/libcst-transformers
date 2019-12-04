import sys
from pathlib import Path

import libcst as cst
from libcst import Module, ImportFrom, SimpleStatementLine, Name, ImportAlias, Expr, SimpleString


class HasFutureAnnotationImport(cst.CSTVisitor):
    has_annotation_import = False

    def leave_ImportFrom_module(self, node: ImportFrom) -> None:
        if node.module.value == "__future__" and any(n for n in node.names if n.name.value == "annotations"):
            self.has_annotation_import = True


class ImportTransformer(cst.CSTTransformer):
    def leave_Module_header(self, node: "Module") -> None:
        if node.body:
            to_insert = SimpleStatementLine(
                body=[ImportFrom(module=Name("__future__"), names=[ImportAlias(name=Name("annotations"))])]
            )
            node.body.insert(1 if self.has_module_docstring(node) else 0, to_insert)

    @staticmethod
    def has_module_docstring(node):
        has_module_docstring = False
        n = node.body[0]
        if isinstance(n, SimpleStatementLine):
            n = n.body[0]
            if isinstance(n, Expr):
                if len(n.children) == 1 and isinstance(n.children[0], SimpleString):
                    has_module_docstring = True
        return has_module_docstring


if __name__ == "__main__":
    filename = sys.argv[1]
    file_path = Path(filename)
    source_tree = cst.parse_module(file_path.read_text())

    visitor = HasFutureAnnotationImport()
    source_tree.visit(visitor)
    if not visitor.has_annotation_import:
        transformer = ImportTransformer()
        modified_tree = source_tree.visit(transformer)
        file_path.write_text(modified_tree.code)
