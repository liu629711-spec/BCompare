object TextFindInFilesDialog: TTextFindInFilesDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgTextFindInFiles'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Find in Files'
  ClientHeight = 265
  ClientWidth = 337
  OnClose = FormClose
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object FindStrLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Text to find:'
    FocusControl = FindStrEdit
  end
  object FindREBtn: TUiSpeedButton
    Left = 306
    Top = 25
    Hint = 'Insert Regular Expression Element'
    DropDown = True
    Flat = False
    PopupMenu = FindREPopup
  end
  object DirLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Folder:'
    FocusControl = DirEdit
  end
  object MaskLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = 'File &mask:'
    FocusControl = MaskEdit
  end
  object FindStrEdit: TUiComboBox
    Left = 8
    Top = 25
    Width = 291
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
    IsMRU = True
  end
  object DirEdit: TUiSpecComboBar
    Left = 8
    Top = 71
    Width = 321
    AutoCompleteEx = acDirs
    Images = BcImages.MainImages
    SupportsProfile = True
    TabOrder = 1
    OnBrowse = DirEditBrowse
    OnChange = SomethingChangedClick
    OnUpdateTitles = DirEditUpdateTitles
  end
  object MaskEdit: TUiComboBox
    Left = 8
    Top = 117
    Width = 321
    Height = 21
    TabOrder = 2
    OnChange = SomethingChangedClick
    IsMRU = True
  end
  object CaseSensitiveEdit: TUiCheckBox
    Left = 8
    Top = 146
    Height = 17
    Caption = 'Match character &case'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object WholeWordsEdit: TUiCheckBox
    Left = 8
    Top = 167
    Height = 17
    Caption = '&Whole words only'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object IsRegExpEdit: TUiCheckBox
    Left = 8
    Top = 188
    Height = 17
    Caption = 'Regular e&xpression'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object REHelpBtn: TUiButton
    Left = 251
    Top = 182
    Width = 78
    HelpType = htKeyword
    HelpKeyword = 'Sample_Regular_Expressions'
    Caption = 'RE Example&s'
    TabOrder = 6
    AutoSize = asRight
  end
  object SubDirsEdit: TUiCheckBox
    Left = 8
    Top = 209
    Height = 17
    Caption = 'Search s&ubfolders'
    TabOrder = 7
    OnClick = SomethingChangedClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 226
    Width = 337
    TabOrder = 8
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
  object FindREPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object TabItem: TUiMenuItem
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
end
