object DirSyncSessionHandlingFrame: TDirSyncSessionHandlingFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionDirSyncHandling'
  Caption = 'Handling'
  object DirHandlingLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Folder handling:'
  end
  object FileHandlingBevel: TUiBevel
    Left = 8
    Top = 92
    Width = 409
    Height = 1
    Shape = bsTopLine
  end
  object FileHandlingLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = 'File handling:'
  end
  object RefreshBevel: TUiBevel
    Left = 8
    Top = 247
    Width = 409
    Height = 1
    Shape = bsTopLine
  end
  object RefreshLbl: TUiLabel
    Left = 8
    Top = 255
    Height = 13
    Caption = 'Automatic &refresh:'
    FocusControl = RefreshIntervalEdit
  end
  object RefreshMinutesLbl: TUiLabel
    Left = 63
    Top = 276
    Height = 13
    Caption = 'minutes'
  end
  object SyncEmptyFoldersEdit: TUiCheckBox
    Left = 8
    Top = 25
    Height = 17
    Caption = 'Sync &empty folders'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object ExpandAllOnLoadEdit: TUiCheckBox
    Left = 8
    Top = 46
    Height = 17
    Caption = 'E&xpand subfolders when loading session'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object ArchiveAsFolderEdit: TUiCheckBox
    Left = 8
    Top = 67
    Height = 17
    Caption = 'Sync within archi&ves (e.g. zip files)'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object UseRecycleBinEdit: TUiCheckBox
    Left = 8
    Top = 117
    Height = 17
    Caption = 'De&lete to recycle bin if possible'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object TouchLocalOnUploadEdit: TUiCheckBox
    Left = 8
    Top = 138
    Height = 17
    Caption = '&Touch local files when copying to an FTP site'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object FollowSymLinksEdit: TUiCheckBox
    Left = 8
    Top = 159
    Height = 17
    Caption = 'Follow s&ymbolic links'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object KeepShortNamesEdit: TUiCheckBox
    Left = 8
    Top = 180
    Height = 17
    Caption = 'Maintain DOS &8.3 aliases'
    TabOrder = 6
    OnClick = SomethingChangedClick
  end
  object CopyACLsEdit: TUiCheckBox
    Left = 8
    Top = 201
    Height = 17
    Caption = 'Copy NTFS file per&missions (requires admin rights)'
    TabOrder = 7
    OnClick = SomethingChangedClick
  end
  object CopyCreationDatesEdit: TUiCheckBox
    Left = 8
    Top = 222
    Height = 17
    Caption = 'Copy creati&on dates'
    TabOrder = 8
    OnClick = SomethingChangedClick
  end
  object RefreshIntervalEdit: TUiSpinEdit
    Left = 8
    Top = 272
    Width = 50
    Height = 21
    Max = 9999
    MaxLength = 4
    TabOrder = 9
    OnChange = SomethingChangedClick
  end
end
