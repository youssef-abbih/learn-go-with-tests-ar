-- Pandoc Lua filter: keep code left-to-right inside a right-to-left Arabic book.
--
-- Every code block and every inline code span is wrapped in an English
-- container. In LaTeX (PDF) pandoc turns lang="en" into babel's
-- otherlanguage / foreignlanguage, which switches the text direction.
-- In HTML (EPUB) the dir="ltr" attribute does the same job.

local function ltr_attr()
  if FORMAT:match("latex") then
    return pandoc.Attr("", {}, { { "lang", "en" } })
  end
  return pandoc.Attr("", {}, { { "lang", "en" }, { "dir", "ltr" } })
end

function CodeBlock(block)
  return pandoc.Div({ block }, ltr_attr())
end

function Code(inline)
  return pandoc.Span({ inline }, ltr_attr())
end
