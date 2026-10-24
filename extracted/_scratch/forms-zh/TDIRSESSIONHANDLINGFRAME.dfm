object DirSessionHandlingFrame: TDirSessionHandlingFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionDirHandling'
  Caption = 'Handling'
  object DirHandlingLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Folder handling:'
  end
  object ArchiveHandlingLbl: TUiLabel
    Left = 8
    Top = 113
    Height = 13
    Caption = 'Archi&ve handling (e.g. zip files):'
    FocusControl = ArchiveHandlingEdit
  end
  object FileHandlingBevel: TUiBevel
    Left = 8
    Top = 159
    Width = 409
    Height = 1
    Shape = bsTopLine
  end
  object FileHandlingLbl: TUiLabel
    Left = 8
    Top = 167
    Height = 13
    Caption = 'File handling:'
  end
  object RefreshLbl: TUiLabel
    Left = 8
    Top = 293
    Height = 13
    Caption = 'Automatic &refresh:'
    FocusControl = RefreshIntervalEdit
  end
  object AutoBuildEdit: TUiCheckBox
    Left = 8
    Top = 25
    Height = 17
    Caption = 'Automatically sca&n subfolders in background'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object AutoBuildTopOrphansEdit: TUiCheckBox
    Left = 24
    Top = 46
    Height = 17
    Caption = 'Automatically scan top-level orp&han subfolders'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object ExpandAllOnLoadEdit: TUiCheckBox
    Left = 8
    Top = 67
    Height = 17
    Caption = 'E&xpand subfolders when loading session'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object ExpandDiffsOnLoadEdit: TUiCheckBox
    Left = 24
    Top = 88
    Height = 17
    Caption = 'Only expand subfolders with di&fferences'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object ArchiveHandlingEdit: TUiComboBox
    Left = 8
    Top = 130
    Width = 146
    Height = 21
    Style = csDropDownList
    TabOrder = 4
    OnChange = SomethingChangedClick
    Items.Strings = ('As files always', 'As folders once opened', 'As folders always')
  end
  object TouchLocalOnUploadEdit: TUiCheckBox
    Left = 8
    Top = 184
    Height = 17
    Caption = '&Touch local files when copying to an FTP site'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object FollowSymLinksEdit: TUiCheckBox
    Left = 8
    Top = 205
    Height = 17
    Caption = 'Follow s&ymbolic links'
    TabOrder = 6
    OnClick = SomethingChangedClick
  end
  object KeepShortNamesEdit: TUiCheckBox
    Left = 8
    Top = 226
    Height = 17
    Caption = 'Maintain DOS &8.3 aliases'
    TabOrder = 7
    OnClick = SomethingChangedClick
  end
  object CopyACLsEdit: TUiCheckBox
    Left = 8
    Top = 247
    Height = 17
    Caption = 'Copy NTFS file per&missions (requires admin rights)'
    TabOrder = 8
    OnClick = SomethingChangedClick
  end
  object CopyCreationDatesEdit: TUiCheckBox
    Left = 8
    Top = 268
    Height = 17
    Caption = 'Copy creati&on dates'
    TabOrder = 9
    OnClick = SomethingChangedClick
  end
  object RefreshIntervalEdit: TUiSpinEdit
    Left = 8
    Top = 310
    Width = 50
    Height = 21
    Max = 9999
    MaxLength = 4
    TabOrder = 10
    OnChange = SomethingChangedClick
  end
  object RefreshGranularityEdit: TUiComboBox
    Left = 64
    Top = 310
    Width = 73
    Height = 21
    Style = csDropDownList
    TabOrder = 11
    OnChange = SomethingChangedClick
    Items.Strings = ('Seconds', 'Minutes')
  end
end
