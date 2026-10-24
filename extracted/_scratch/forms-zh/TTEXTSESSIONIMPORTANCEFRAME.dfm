object TextSessionImportanceFrame: TTextSessionImportanceFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionTextImportance'
  Caption = 'Importance'
  object InsigsLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Unimportant text:'
    FocusControl = InsigsListBox
  end
  object SigsLbl: TUiLabel
    Left = 8
    Top = 157
    Height = 13
    Caption = 'Mark &grammar elements that are important to the comparison:'
    FocusControl = SigsListBox
  end
  object LeftGrammarLbl: TUiLabel
    Left = 324
    Top = 174
    Height = 13
    Caption = '%'
    FocusControl = LeftGrammarEditBtn
  end
  object RightGrammarLbl: TUiLabel
    Left = 324
    Top = 222
    Height = 13
    Caption = '%'
    FocusControl = RightGrammarEditBtn
  end
  object InsigsListBox: TUiListBox
    Left = 8
    Top = 25
    Width = 409
    Height = 93
    DragMode = dmAutomatic
    TabOrder = 0
    OnClick = InsigsListBoxClick
    OnDblClick = InsigsEditClick
    OnDragDrop = InsigsListBoxDragDrop
    OnDragOver = InsigsListBoxDragOver
    OnKeyDown = InsigsListBoxKeyDown
  end
  object InsigsNewBtn: TUiBitBtn
    Left = 8
    Top = 126
    Width = 24
    Hint = 'New'
    ImageIndex = imgListAdd
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = InsigsNewClick
  end
  object InsigsDeleteBtn: TUiBitBtn
    Left = 32
    Top = 126
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = InsigsDeleteClick
  end
  object InsigsEditBtn: TUiBitBtn
    Left = 56
    Top = 126
    Width = 24
    Hint = 'Edit'
    ImageIndex = imgListEdit
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = InsigsEditClick
  end
  object InsigsCloneBtn: TUiBitBtn
    Left = 80
    Top = 126
    Width = 24
    Hint = 'Clone'
    ImageIndex = imgListClone
    Images = BcImages.MainImages
    TabOrder = 4
    OnClick = InsigsCloneClick
  end
  object SigsListBox: TUiCheckListBox
    Left = 8
    Top = 174
    Width = 308
    Height = 132
    OnClickCheck = SomethingChangedClick
    TabOrder = 5
  end
  object LeftGrammarEditBtn: TUiButton
    Left = 324
    Top = 191
    Caption = '&Edit Grammar...'
    TabOrder = 6
    OnClick = GrammarEditClick
    AutoSize = asLeft
  end
  object RightGrammarEditBtn: TUiButton
    Left = 324
    Top = 239
    Caption = 'Edi&t Grammar...'
    TabOrder = 7
    OnClick = GrammarEditClick
    AutoSize = asLeft
  end
  object OrphansAlwaysSigEdit: TUiCheckBox
    Left = 8
    Top = 314
    Height = 17
    Caption = '&Orphan lines are always important'
    TabOrder = 8
    OnClick = SomethingChangedClick
  end
  object CompareEndingsEdit: TUiCheckBox
    Left = 8
    Top = 335
    Height = 17
    Caption = 'Com&pare line endings (PC/Mac/Unix)'
    TabOrder = 9
    OnClick = SomethingChangedClick
  end
end
