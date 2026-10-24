object DirSyncSessionOpsFrame: TDirSyncSessionOpsFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionDirSyncOps'
  Caption = 'Sync'
  object PresetLbl: TUiLabel
    Left = 32
    Top = 12
    Height = 13
    Caption = '&Presets:'
    FocusControl = PresetEdit
  end
  object LeftNewerImage: TUiImage
    Left = 8
    Top = 38
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object LeftNewerLbl: TUiLabel
    Left = 32
    Top = 40
    Height = 13
    Caption = 'If file on left is &newer:'
    FocusControl = LeftNewerEdit
  end
  object RightNewerImage: TUiImage
    Left = 8
    Top = 63
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object RightNewerLbl: TUiLabel
    Left = 32
    Top = 65
    Height = 13
    Caption = 'If file on right is ne&wer:'
    FocusControl = RightNewerEdit
  end
  object LeftAddedImage: TUiImage
    Left = 8
    Top = 88
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object LeftAddedLbl: TUiLabel
    Left = 32
    Top = 90
    Height = 13
    Caption = 'If file was add&ed on left:'
    FocusControl = LeftAddedEdit
  end
  object RightAddedImage: TUiImage
    Left = 8
    Top = 113
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object RightAddedLbl: TUiLabel
    Left = 32
    Top = 115
    Height = 13
    Caption = 'If file was added on &right:'
    FocusControl = RightAddedEdit
  end
  object LeftDeletedImage: TUiImage
    Left = 8
    Top = 138
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object LeftDeletedLbl: TUiLabel
    Left = 32
    Top = 140
    Height = 13
    Caption = 'If file was de&leted on left:'
    FocusControl = LeftDeletedEdit
  end
  object RightDeletedImage: TUiImage
    Left = 8
    Top = 163
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object RightDeletedLbl: TUiLabel
    Left = 32
    Top = 165
    Height = 13
    Caption = 'If file was dele&ted on right:'
    FocusControl = RightDeletedEdit
  end
  object DiffImage: TUiImage
    Left = 8
    Top = 188
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object DiffLbl: TUiLabel
    Left = 32
    Top = 190
    Height = 13
    Caption = 'If files are di&fferent:'
    FocusControl = DiffEdit
  end
  object SameImage: TUiImage
    Left = 8
    Top = 213
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object SameLbl: TUiLabel
    Left = 32
    Top = 215
    Height = 13
    Caption = 'If files are the sa&me:'
    FocusControl = SameEdit
  end
  object SyncMemoryDescLbl: TUiLabel
    Left = 8
    Top = 240
    Width = 409
    Height = 26
    Caption = 'Sync Memory remembers the state after each sync in order to detect deleted files and conflicting changes.'
    WordWrap = True
  end
  object PresetEdit: TUiComboBox
    Left = 170
    Top = 8
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    OnChange = PresetEditChange
    Images = BcImages.MainImages
    OnGetImageIndex = PresetEditGetImageIndex
  end
  object LeftNewerEdit: TUiComboBox
    Left = 170
    Top = 36
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 1
    OnChange = StatusEditChange
  end
  object RightNewerEdit: TUiComboBox
    Left = 170
    Top = 61
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 2
    OnChange = StatusEditChange
  end
  object LeftAddedEdit: TUiComboBox
    Left = 170
    Top = 86
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 3
    OnChange = StatusEditChange
  end
  object RightAddedEdit: TUiComboBox
    Left = 170
    Top = 111
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 4
    OnChange = StatusEditChange
  end
  object LeftDeletedEdit: TUiComboBox
    Left = 170
    Top = 136
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 5
    OnChange = StatusEditChange
  end
  object RightDeletedEdit: TUiComboBox
    Left = 170
    Top = 161
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 6
    OnChange = StatusEditChange
  end
  object DiffEdit: TUiComboBox
    Left = 170
    Top = 186
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 7
    OnChange = StatusEditChange
  end
  object SameEdit: TUiComboBox
    Left = 170
    Top = 211
    Width = 247
    Height = 21
    Style = csDropDownList
    TabOrder = 8
    OnChange = StatusEditChange
  end
  object UseSyncMemoryEdit: TUiCheckBox
    Left = 8
    Top = 270
    Height = 17
    Caption = '&Use Sync Memory'
    TabOrder = 9
    OnClick = SomethingChangedClick
  end
  object ClearMemoryBtn: TUiButton
    Left = 334
    Top = 270
    Width = 83
    Caption = '&Clear Memory'
    TabOrder = 10
    OnClick = ClearMemoryClick
    AutoSize = asRight
  end
end
