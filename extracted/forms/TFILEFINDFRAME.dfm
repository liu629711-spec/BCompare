object FileFindFrame: TFileFindFrame
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
  object FindStrLbl: TUiLabel
    Left = 18
    Top = 8
    Height = 13
    Caption = 'Find what:'
  end
  object FindREBtn: TUiSpeedButton
    Left = 505
    Top = 4
    Hint = 'Insert Regular Expression Element'
    DropDown = True
    Flat = False
    PopupMenu = FindREPopup
  end
  object ReplaceStrLbl: TUiLabel
    Left = 4
    Top = 34
    Height = 13
    Caption = 'Replace with:'
  end
  object ReplaceREBtn: TUiSpeedButton
    Left = 505
    Top = 30
    Hint = 'Insert Regular Expression Element'
    DropDown = True
    Flat = False
    PopupMenu = ReplaceREPopup
  end
  object SidesLbl: TUiLabel
    Left = 40
    Top = 60
    Height = 13
    Caption = 'Sides:'
  end
  object IsRegExpBtn: TUiSpeedButton
    Left = 536
    Top = 4
    Hint = 'Regular Expression'
    AutoCheck = True
    Flat = False
    ImageIndex = imgFindIsRegExp
    Images = BcImages.MainImages
    OnClick = SomethingChangedClick
  end
  object CaseSensitiveBtn: TUiSpeedButton
    Left = 559
    Top = 4
    Hint = 'Match Character Case'
    AutoCheck = True
    Flat = False
    ImageIndex = imgFindCaseSensitive
    Images = BcImages.MainImages
    OnClick = SomethingChangedClick
  end
  object WholeWordsBtn: TUiSpeedButton
    Left = 582
    Top = 4
    Hint = 'Whole Words Only'
    AutoCheck = True
    Flat = False
    ImageIndex = imgFindWholeWords
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
  object FindStrEdit: TUiComboBox
    Left = 73
    Top = 5
    Width = 428
    Height = 21
    TabOrder = 0
    OnChange = FindStrEditChange
    IsMRU = True
  end
  object ReplaceStrEdit: TUiComboBox
    Left = 73
    Top = 31
    Width = 428
    Height = 21
    TabOrder = 1
    OnChange = SomethingChangedClick
    IsMRU = True
  end
  object SidesEdit: TUiComboBox
    Left = 73
    Top = 57
    Width = 114
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
  object SelectAllBtn: TUiButton
    Left = 655
    Top = 56
    Caption = 'Select &All'
    TabOrder = 7
    OnClick = SelectAllClick
    AutoSize = asLeft
    AutoSizeMinWidth = 0
  end
  object AutoCloseEdit: TUiCheckBox
    Left = 536
    Top = 59
    Height = 17
    Caption = 'Close automaticall&y'
    TabOrder = 8
    OnClick = FindStrEditChange
  end
  object FindREPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object FindTabItem: TUiMenuItem
      Caption = 'Tab Character (\t)'
      OnClick = FindREItemClick
    end
    object AnyItem: TUiMenuItem
      Caption = 'Any Character (.)'
      OnClick = FindREItemClick
    end
    object AlphaItem: TUiMenuItem
      Caption = 'Any Alphanumeric Character (\w)'
      OnClick = FindREItemClick
    end
    object NonAlphaItem: TUiMenuItem
      Caption = 'Any Non-alphanumeric Character (\W)'
      OnClick = FindREItemClick
    end
    object NumItem: TUiMenuItem
      Caption = 'Any Numeric Character (\d)'
      OnClick = FindREItemClick
    end
    object NonNumItem: TUiMenuItem
      Caption = 'Any Non-numeric Character (\D)'
      OnClick = FindREItemClick
    end
    object WSItem: TUiMenuItem
      Caption = 'Any Whitespace Character (\s)'
      OnClick = FindREItemClick
    end
    object CharSetItem: TUiMenuItem
      Caption = 'Character in Set ([])'
      OnClick = FindREItemClick
    end
    object NotCharSetItem: TUiMenuItem
      Caption = 'Character Not in Set ([^])'
      OnClick = FindREItemClick
    end
    object BeginItem: TUiMenuItem
      Caption = 'Beginning of Line (^)'
      OnClick = FindREItemClick
    end
    object EndItem: TUiMenuItem
      Caption = 'End of Line ($)'
      OnClick = FindREItemClick
    end
    object TaggedItem: TUiMenuItem
      Caption = 'Tagged Expression (())'
      OnClick = FindREItemClick
    end
    object OrItem: TUiMenuItem
      Caption = 'Or (|)'
      OnClick = FindREItemClick
    end
    object ZeroOrMoreItem: TUiMenuItem
      Caption = '0 Or More Matches (*)'
      OnClick = FindREItemClick
    end
    object OneOrMoreItem: TUiMenuItem
      Caption = '1 Or More Matches (+)'
      OnClick = FindREItemClick
    end
    object ZeroOrOneItem: TUiMenuItem
      Caption = '0 Or 1 Matches (?)'
      OnClick = FindREItemClick
    end
  end
  object ReplaceREPopup: TUiPopupMenu
    Left = 40
    Top = 8
    object ReplaceTabItem: TUiMenuItem
      Caption = 'Tab Character (\t)'
      OnClick = ReplaceREItemClick
    end
    object FindStrItem: TUiMenuItem
      Caption = 'Find Expression ($0)'
      OnClick = ReplaceREItemClick
    end
    object Tagged1Item: TUiMenuItem
      Caption = 'Tagged Expression 1 ($1)'
      OnClick = ReplaceREItemClick
    end
    object Tagged2Item: TUiMenuItem
      Caption = 'Tagged Expression 2 ($2)'
      OnClick = ReplaceREItemClick
    end
    object Tagged3Item: TUiMenuItem
      Caption = 'Tagged Expression 3 ($3)'
      OnClick = ReplaceREItemClick
    end
    object Tagged4Item: TUiMenuItem
      Caption = 'Tagged Expression 4 ($4)'
      OnClick = ReplaceREItemClick
    end
    object Tagged5Item: TUiMenuItem
      Caption = 'Tagged Expression 5 ($5)'
      OnClick = ReplaceREItemClick
    end
    object Tagged6Item: TUiMenuItem
      Caption = 'Tagged Expression 6 ($6)'
      OnClick = ReplaceREItemClick
    end
    object Tagged7Item: TUiMenuItem
      Caption = 'Tagged Expression 7 ($7)'
      OnClick = ReplaceREItemClick
    end
    object Tagged8Item: TUiMenuItem
      Caption = 'Tagged Expression 8 ($8)'
      OnClick = ReplaceREItemClick
    end
    object Tagged9Item: TUiMenuItem
      Caption = 'Tagged Expression 9 ($9)'
      OnClick = ReplaceREItemClick
    end
  end
end
