object FileSessionSpecsFrame: TFileSessionSpecsFrame
  Caption = 'Specs'
  object LeftLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Left file:'
    FocusControl = LeftEdit
  end
  object RightLbl: TUiLabel
    Left = 8
    Top = 71
    Height = 13
    Caption = '&Right file:'
    FocusControl = RightEdit
  end
  object CenterLbl: TUiLabel
    Left = 8
    Top = 134
    Height = 13
    Caption = '&Center file:'
    FocusControl = CenterEdit
  end
  object DescriptionLbl: TUiLabel
    Left = 8
    Top = 243
    Height = 13
    Caption = 'D&escription:'
    FocusControl = DescriptionEdit
  end
  object LastModifiedLbl: TUiLabel
    Left = 8
    Top = 339
    Height = 13
    Caption = '%'
  end
  object LeftEdit: TUiSpecComboBar
    Left = 8
    Top = 25
    Width = 409
    AllowDropFiles = False
    Images = BcImages.MainImages
    SupportsProfile = True
    TabOrder = 0
    OnBrowse = EditBrowse
    OnChange = SomethingChangedClick
    OnDropDown = EditDropDown
    OnUpdateTitles = EditUpdateTitles
  end
  object LeftNoEditEdit: TUiCheckBox
    Left = 8
    Top = 50
    Height = 17
    Caption = 'D&isable editing'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object CopyBtn: TUiBitBtn
    Left = 184
    Top = 50
    Width = 24
    Hint = 'Copy Left to Right'
    ImageIndex = imgDown
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = CopyClick
  end
  object SwapBtn: TUiBitBtn
    Left = 216
    Top = 50
    Width = 24
    Hint = 'Swap Sides'
    ImageIndex = imgSwap
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = SwapClick
  end
  object RightEdit: TUiSpecComboBar
    Left = 8
    Top = 88
    Width = 409
    AllowDropFiles = False
    Images = BcImages.MainImages
    SupportsProfile = True
    TabOrder = 4
    OnBrowse = EditBrowse
    OnChange = SomethingChangedClick
    OnDropDown = EditDropDown
    OnUpdateTitles = EditUpdateTitles
  end
  object RightNoEditEdit: TUiCheckBox
    Left = 8
    Top = 113
    Height = 17
    Caption = 'Disable edi&ting'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object CenterEdit: TUiSpecComboBar
    Left = 8
    Top = 151
    Width = 409
    AllowDropFiles = False
    Images = BcImages.MainImages
    SupportsProfile = True
    TabOrder = 6
    OnBrowse = EditBrowse
    OnChange = SomethingChangedClick
    OnDropDown = EditDropDown
    OnUpdateTitles = EditUpdateTitles
  end
  object MergeSidePanel: TUiPanel
    Left = 8
    Top = 193
    Width = 409
    Height = 17
    BevelOuter = bvNone
    TabOrder = 7
    object MergeSideLbl: TUiLabel
      Left = 0
      Top = 2
      Height = 13
      Caption = '&Merge to:'
      FocusControl = OutputEdit
    end
    object MergeLeftEdit: TUiRadioButton
      Left = 102
      Top = 0
      Height = 17
      Caption = 'Le&ft'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object MergeRightEdit: TUiRadioButton
      Left = 204
      Top = 0
      Height = 17
      Caption = 'Ri&ght'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
    object MergeOutputEdit: TUiRadioButton
      Left = 306
      Top = 0
      Height = 17
      Caption = 'Ot&her:'
      TabOrder = 2
      OnClick = SomethingChangedClick
    end
  end
  object OutputEdit: TUiSpecComboBar
    Left = 8
    Top = 214
    Width = 409
    AllowDropFiles = False
    Images = BcImages.MainImages
    SupportsProfile = True
    TabOrder = 8
    OnBrowse = EditBrowse
    OnChange = SomethingChangedClick
    OnDropDown = EditDropDown
    OnUpdateTitles = EditUpdateTitles
  end
  object DescriptionEdit: TUiMemo
    Left = 8
    Top = 260
    Width = 409
    Height = 75
    ScrollBars = ssVertical
    TabOrder = 9
    OnChange = SomethingChangedClick
  end
end
