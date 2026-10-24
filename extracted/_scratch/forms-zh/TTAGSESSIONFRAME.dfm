object TagSessionFrame: TTagSessionFrame
  HelpType = htKeyword
  Caption = 'Importance'
  object SigsLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Mark &items that are important to the comparison:'
    FocusControl = SigsListBox
  end
  object SigsListBox: TUiCheckListBox
    Left = 8
    Top = 25
    Width = 409
    Height = 296
    OnClickCheck = SomethingChangedClick
    TabOrder = 0
    OnGetNotLast = SigsListBoxGetNotLast
  end
  object SigAllBtn: TUiBitBtn
    Left = 8
    Top = 329
    Width = 24
    Hint = 'Mark All'
    ImageIndex = imgCheckAll
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = SigAllClick
  end
  object SigNoneBtn: TUiBitBtn
    Left = 32
    Top = 329
    Width = 24
    Hint = 'Unmark All'
    ImageIndex = imgUncheckAll
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = SigNoneClick
  end
end
