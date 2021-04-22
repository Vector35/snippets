#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Licensed under the terms of the MIT License

Re-written for Snippet Editor by Jordan Wiens (https://github.com/psifertex/)
With some original components (line numbers) based on: 

https://github.com/luchko/QCodeEditor
@author: Ivan Luchko (luchko.ivan@gmail.com)
'''

import binaryninjaui
from binaryninja import log_warn
if "qt_major_version" in binaryninjaui.__dict__ and binaryninjaui.qt_major_version == 6:
    from PySide6.QtCore import Qt, QRect, QRegularExpression
    from PySide6.QtWidgets import QWidget, QTextEdit, QPlainTextEdit
    from PySide6.QtGui import (QPainter, QFont, QSyntaxHighlighter, QTextFormat, QTextCharFormat, QColor)
else:
    from PySide2.QtCore import Qt, QRect, QRegularExpression
    from PySide2.QtWidgets import QWidget, QTextEdit, QPlainTextEdit
    from PySide2.QtGui import (QPainter, QFont, QSyntaxHighlighter, QTextFormat, QTextCharFormat, QColor)
from binaryninjaui import (getMonospaceFont, getThemeColor, ThemeColor)
from pygments import highlight, token
from pygments.lexers import *
from pygments.formatter import Formatter


def bnformat(color, style=''):
    """Return a QTextCharFormat with the given attributes."""
    color = eval('getThemeColor(ThemeColor.%s)' % color)

    format = QTextCharFormat()
    format.setForeground(color)
    if 'bold' in style:
        format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        format.setFontItalic(True)

    return format

# Most of these aren't needed but after fighting pygments for so long I figure they can't hurt. 
bnstyles = {
    'Token.Literal.Number': bnformat('NumberColor'),
    'Token.Literal.Number.Bin': bnformat('NumberColor'),
    'Token.Literal.Number.Float': bnformat('NumberColor'),
    'Token.Literal.Number.Integer': bnformat('NumberColor'),
    'Token.Literal.Number.Integer.Long': bnformat('NumberColor'),
    'Token.Literal.Number.Hex': bnformat('NumberColor'),
    'Token.Literal.Number.Oct': bnformat('NumberColor'),

    'Token.Literal.String': bnformat('StringColor'),
    'Token.Literal.String.Single': bnformat('StringColor'),
    'Token.Literal.String.Char': bnformat('StringColor'),
    'Token.Literal.String.Backtick': bnformat('StringColor'),
    'Token.Literal.String.Delimiter': bnformat('StringColor'),
    'Token.Literal.String.Double': bnformat('StringColor'),
    'Token.Literal.String.Heredoc': bnformat('StringColor'),
    'Token.Literal.String.Affix': bnformat('StringColor'),
    'Token.String': bnformat('StringColor'),

    'Token.Comment': bnformat('CommentColor', 'italic'),
    'Token.Comment.Hashbang': bnformat('CommentColor', 'italic'),
    'Token.Comment.Single': bnformat('CommentColor', 'italic'),
    'Token.Comment.Special': bnformat('CommentColor', 'italic'),
    'Token.Comment.PreprocFile': bnformat('CommentColor', 'italic'),
    'Token.Comment.Multiline': bnformat('CommentColor', 'italic'),

    'Token.Keyword': bnformat('StackVariableColor'),

    'Token.Operator': bnformat('TokenHighlightColor'),
    'Token.Punctuation': bnformat('LinearDisassemblySeparatorColor'),

    #This is the most important and hardest to get right. No way to get theme palettes!
    'Token.Name': bnformat('OutlineColor'), 

    'Token.Name.Namespace': bnformat('OutlineColor'),

    'Token.Name.Variable': bnformat('DataSymbolColor'),
    'Token.Name.Class': bnformat('DataSymbolColor'),
    'Token.Name.Constant': bnformat('DataSymbolColor'),
    'Token.Name.Entity': bnformat('DataSymbolColor'),
    'Token.Name.Other': bnformat('DataSymbolColor'),
    'Token.Name.Tag': bnformat('DataSymbolColor'),
    'Token.Name.Decorator': bnformat('DataSymbolColor'),
    'Token.Name.Label': bnformat('DataSymbolColor'),
    'Token.Name.Variable.Magic': bnformat('DataSymbolColor'),
    'Token.Name.Variable.Instance': bnformat('DataSymbolColor'),
    'Token.Name.Variable.Class': bnformat('DataSymbolColor'),
    'Token.Name.Variable.Global': bnformat('DataSymbolColor'),
    'Token.Name.Property': bnformat('DataSymbolColor'),
    'Token.Name.Function': bnformat('DataSymbolColor'),
    'Token.Name.Builtin': bnformat('ImportColor'),
    'Token.Name.Builtin.Pseudo': bnformat('ImportColor'),

    'Token.Escape': bnformat('ImportColor'),

    'Token.Keyword': bnformat('GotoLabelColor'),
    'Token.Operator.Word': bnformat('GotoLabelColor'),

    'numberBar': getThemeColor(ThemeColor.BackgroundHighlightDarkColor),
    'blockSelected': getThemeColor(ThemeColor.TokenHighlightColor),
    'blockNormal': getThemeColor(ThemeColor.TokenSelectionColor),
}

class QFormatter(Formatter):

    def __init__(self):
        Formatter.__init__(self)
        self.pygstyles={}
        for token, style in self.style:
            tokenname = str(token)
            if tokenname in bnstyles.keys():
                self.pygstyles[str(token)]=bnstyles[tokenname]
                #log_warn("MATCH: %s with %s" % (tokenname, str(token)))
            else:
                self.pygstyles[str(token)]=bnstyles['Token.Name']
                #log_warn("NONE: %s with %s" % (tokenname, str(token)))

    def format(self, tokensource, outfile):
        self.data=[]
        for token, value in tokensource:
            self.data.extend([self.pygstyles[str(token)],]*len(value))

class Pylighter(QSyntaxHighlighter):

    def __init__(self, parent, lang):
        QSyntaxHighlighter.__init__(self, parent)
        self.formatter=QFormatter()
        self.lexer=get_lexer_by_name(lang)

    def highlightBlock(self, text):
        cb = self.currentBlock()
        p = cb.position()
        text=self.document().toPlainText()
        highlight(text,self.lexer,self.formatter)
        
        #dirty, dirty hack
        for i in range(len(text)):
            try:
                self.setFormat(i,1,self.formatter.data[p+i])
            except IndexError:
                pass


class QCodeEditor(QPlainTextEdit):
    class NumberBar(QWidget):

        def __init__(self, editor):
            QWidget.__init__(self, editor)
            global bnstyles

            self.editor = editor
            self.editor.blockCountChanged.connect(self.updateWidth)
            self.editor.updateRequest.connect(self.updateContents)
            self.font = QFont()
            self.numberBarColor = bnstyles["numberBar"]

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(event.rect(), self.numberBarColor)

            block = self.editor.firstVisibleBlock()

            # Iterate over all visible text blocks in the document.
            while block.isValid():
                blockNumber = block.blockNumber()
                block_top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()

                # Check if the position of the block is out side of the visible area.
                if not block.isVisible() or block_top >= event.rect().bottom():
                    break

                # We want the line number for the selected line to be bold.
                if blockNumber == self.editor.textCursor().blockNumber():
                    self.font.setBold(True)
                    painter.setPen(bnstyles["blockSelected"])
                else:
                    self.font.setBold(False)
                    painter.setPen(bnstyles["blockNormal"])
                painter.setFont(self.font)

                # Draw the line number right justified at the position of the line.
                paint_rect = QRect(0, block_top, self.width(), self.editor.fontMetrics().height())
                painter.drawText(paint_rect, Qt.AlignLeft, str(blockNumber+1))

                block = block.next()

            painter.end()

            QWidget.paintEvent(self, event)

        def getWidth(self):
            count = self.editor.blockCount()
            width = self.fontMetrics().horizontalAdvance(str(count)) + 10
            return width

        def updateWidth(self):
            width = self.getWidth()
            if self.width() != width:
                self.setFixedWidth(width)
                self.editor.setViewportMargins(width, 0, 0, 0)

        def updateContents(self, rect, scroll):
            if scroll:
                self.scroll(0, scroll)
            else:
                self.update(0, rect.y(), self.width(), rect.height())

            if rect.contains(self.editor.viewport().rect()):
                fontSize = self.editor.currentCharFormat().font().pointSize()
                self.font.setPointSize(fontSize)
                self.font.setStyle(QFont.StyleNormal)
                self.updateWidth()


    def __init__(self, DISPLAY_LINE_NUMBERS=True, HIGHLIGHT_CURRENT_LINE=True,
                 SyntaxHighlighter=Pylighter, lang="python", font_size=11, *args):
        super(QCodeEditor, self).__init__()

        font = getMonospaceFont(self)
        font.setPointSize(font_size)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.DISPLAY_LINE_NUMBERS = DISPLAY_LINE_NUMBERS

        if DISPLAY_LINE_NUMBERS:
            self.number_bar = self.NumberBar(self)

        if SyntaxHighlighter is not None: # add highlighter to textdocument
            self.highlighter = SyntaxHighlighter(self.document(), lang)

    def resizeEvent(self, *e):
        '''overload resizeEvent handler'''

        if self.DISPLAY_LINE_NUMBERS:   # resize number_bar widget
            cr = self.contentsRect()
            rec = QRect(cr.left(), cr.top(), self.number_bar.getWidth(), cr.height())
            self.number_bar.setGeometry(rec)

        QPlainTextEdit.resizeEvent(self, *e)
