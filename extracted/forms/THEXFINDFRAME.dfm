object HexFindFrame: THexFindFrame
  Left = 0
  Top = 0
  Width = 750
  Height = 82
  TabOrder = 0
  object FindImage: TUiImage
    Left = 8
    Top = 8
    Width = 16
    Height = 16
    ImageIndex = imgSearch
    Images = BcImages.MainImages
  end
  object FindBytesLbl: TUiLabel
    Left = 18
    Top = 8
    Height = 13
    Caption = 'Find what:'
  end
  object FindMRUBtn: TUiSpeedButton
    Left = 551
    Top = 4
    Hint = 'History'
    DropDown = True
    Flat = False
    PopupMenu = FindMRUPopup
  end
  object ReplaceBytesLbl: TUiLabel
    Left = 4
    Top = 34
    Height = 13
    Caption = 'Replace with:'
  end
  object ReplaceMRUBtn: TUiSpeedButton
    Left = 551
    Top = 30
    Hint = 'History'
    DropDown = True
    Flat = False
    PopupMenu = ReplaceMRUPopup
  end
  object SidesLbl: TUiLabel
    Left = 40
    Top = 60
    Height = 13
    Caption = 'Sides:'
  end
  object CaseSensitiveBtn: TUiSpeedButton
    Left = 582
    Top = 4
    Hint = 'Match Character Case'
    AutoCheck = True
    Flat = False
    ImageIndex = imgFindCaseSensitive
    Images = BcImages.MainImages
    OnClick = SomethingChangedClick
  end
  object WrapBtn: TUiSpeedButton
    Left = 605
    Top = 4
    Hint = 'Wrap Search'
    AutoCheck = True
    Flat = False
    ImageIndex = imgFindWrap
    Images = BcImages.MainImages
    OnClick = SomethingChangedClick
  end
  object AdvancedBtn: TUiShowMoreButton
    Left = 723
    Top = 4
    OnClick = AdvancedClick
  end
  object FindBytesEdit: TUiSimpleHexEditor
    Left = 73
    Top = 5
    Width = 474
    Height = 21
    GroupByteCount = 1
    GroupCountDetect = True
    ScrollBars = ssVertical
    TabOrder = 0
    OnChanged = FindBytesEditChanged
  end
  object ReplaceBytesEdit: TUiSimpleHexEditor
    Left = 73
    Top = 31
    Width = 474
    Height = 21
    GroupByteCount = 1
    GroupCountDetect = True
    ScrollBars = ssVertical
    TabOrder = 1
    OnChanged = SomethingChangedClick
  end
  object SidesEdit: TUiComboBox
    Left = 73
    Top = 57
    Width = 106
    Height = 21
    Style = csDropDownList
    TabOrder = 2
    OnChange = SomethingChangedClick
  end
  object FindPrevBtn: TUiButton
    Left = 636
    Top = 4
    Caption = 'Prev'
    TabOrder = 3
    OnClick = FindPrevClick
    AutoSize = asLeft
    AutoSizeMinWidth = 0
  end
  object FindNextBtn: TUiButton
    Left = 675
    Top = 4
    Caption = 'Next'
    TabOrder = 4
    OnClick = FindNextClick
    AutoSize = asLeft
    AutoSizeMinWidth = 0
  end
  object ReplaceBtn: TUiButton
    Left = 591
    Top = 30
    Caption = 'Replace'
    TabOrder = 5
    OnClick = ReplaceClick
    AutoSize = asLeft
    AutoSizeMinWidth = 0
  end
  object ReplaceAllBtn: TUiButton
    Left = 646
    Top = 30
    Caption = 'Replace &All'
    TabOrder = 6
    OnClick = ReplaceAllClick
    AutoSize = asLeft
    AutoSizeMinWidth = 0
  end
  object AutoCloseEdit: TUiCheckBox
    Left = 582
    Top = 59
    Height = 17
    Caption = 'Close automaticall&y'
    TabOrder = 7
    OnClick = FindBytesEditChanged
  end
  object FindMRUPopup: TUiPopupMenu
    OnPopup = FindMRUPopupPopup
    Left = 8
    Top = 8
  end
  object ReplaceMRUPopup: TUiPopupMenu
    OnPopup = ReplaceMRUPopupPopup
    Left = 40
    Top = 8
  end
end
