object DirSessionNameFilterFrame: TDirSessionNameFilterFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionDirNameFilter'
  Caption = 'Name Filters'
  object IncludeFilesLbl: TUiLabel
    Left = 28
    Top = 8
    Height = 13
    Caption = 'Include &files:'
    FocusControl = IncludeFilesEdit
    Transparent = True
  end
  object ExcludeFilesLbl: TUiLabel
    Left = 236
    Top = 8
    Height = 13
    Caption = 'Exclude fi&les:'
    FocusControl = ExcludeFilesEdit
    Transparent = True
  end
  object IncludeFilesImage: TUiImage
    Left = 8
    Top = 8
    Width = 16
    Height = 16
    ImageIndex = imgNameFilterIncludeFiles
    Images = BcImages.MainImages
  end
  object ExcludeFilesImage: TUiImage
    Left = 216
    Top = 8
    Width = 16
    Height = 16
    ImageIndex = imgNameFilterExcludeFiles
    Images = BcImages.MainImages
  end
  object IncludeFoldersLbl: TUiLabel
    Left = 28
    Top = 192
    Height = 13
    Caption = 'Include f&olders:'
    FocusControl = IncludeFoldersEdit
    Transparent = True
  end
  object ExcludeFoldersLbl: TUiLabel
    Left = 236
    Top = 192
    Height = 13
    Caption = 'Exclude fold&ers:'
    FocusControl = ExcludeFoldersEdit
    Transparent = True
  end
  object IncludeFoldersImage: TUiImage
    Left = 8
    Top = 192
    Width = 16
    Height = 16
    ImageIndex = imgNameFilterIncludeDirs
    Images = BcImages.MainImages
  end
  object ExcludeFoldersImage: TUiImage
    Left = 216
    Top = 192
    Width = 16
    Height = 16
    ImageIndex = imgNameFilterExcludeDirs
    Images = BcImages.MainImages
  end
  object IncludeFilesEdit: TUiMemo
    Left = 8
    Top = 28
    Width = 200
    Height = 156
    ScrollBars = ssVertical
    TabOrder = 0
    WordWrap = False
    OnChange = SomethingChangedClick
  end
  object ExcludeFilesEdit: TUiMemo
    Left = 216
    Top = 28
    Width = 201
    Height = 156
    ScrollBars = ssVertical
    TabOrder = 1
    WordWrap = False
    OnChange = SomethingChangedClick
  end
  object IncludeFoldersEdit: TUiMemo
    Left = 8
    Top = 212
    Width = 200
    Height = 109
    ScrollBars = ssVertical
    TabOrder = 2
    WordWrap = False
    OnChange = SomethingChangedClick
  end
  object ExcludeFoldersEdit: TUiMemo
    Left = 216
    Top = 212
    Width = 201
    Height = 109
    ScrollBars = ssVertical
    TabOrder = 3
    WordWrap = False
    OnChange = SomethingChangedClick
  end
  object DefaultBtn: TUiButton
    Left = 8
    Top = 329
    Caption = '&Clear'
    TabOrder = 4
    OnClick = DefaultClick
  end
  object PresetsNewBtn: TUiButton
    Left = 88
    Top = 329
    Caption = 'Add To &Presets...'
    TabOrder = 5
    OnClick = PresetsNewClick
    AutoSize = asLeft
  end
end
