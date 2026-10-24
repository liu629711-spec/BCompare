object VfsAmazonS3ProfileGeneralFrame: TVfsAmazonS3ProfileGeneralFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileAmazonS3'
  Caption = 'General'
  object AuthTypeLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'A&uthentication type:'
    FocusControl = AuthTypeEdit
  end
  object BucketLbl: TUiLabel
    Left = 8
    Top = 146
    Height = 13
    Caption = '&Bucket (optional):'
    FocusControl = BucketEdit
  end
  object DescriptionLbl: TUiLabel
    Left = 8
    Top = 192
    Height = 13
    Caption = 'D&escription:'
    FocusControl = DescriptionEdit
  end
  object AuthTypeEdit: TUiComboBox
    Left = 8
    Top = 25
    Width = 239
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    OnChange = AuthTypeEditChange
    Items.Strings = ('Saved S3 credentials', 'Load from credentials file', 'Load from environment variables')
  end
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 54
    Width = 255
    Height = 92
    TabOrder = 1
    object ProfilePanel: TUiActivePanel
      object AccessKeyIDLbl: TUiLabel
        Left = 8
        Top = 0
        Height = 13
        Caption = 'Access key &ID:'
        FocusControl = AccessKeyIDEdit
      end
      object SecretAccessKeyLbl: TUiLabel
        Left = 8
        Top = 46
        Height = 13
        Caption = '&Secret access key:'
        FocusControl = SecretAccessKeyEdit
      end
      object AccessKeyIDEdit: TUiEdit
        Left = 8
        Top = 17
        Width = 239
        Height = 21
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
      object SecretAccessKeyEdit: TUiEdit
        Left = 8
        Top = 63
        Width = 239
        Height = 21
        TabOrder = 1
        OnChange = SomethingChangedClick
        EchoMode = emPassword
      end
    end
    object CredFilePanel: TUiActivePanel
      object CredFilePathLbl: TUiLabel
        Left = 8
        Top = 0
        Height = 13
        Caption = '&Credentials or config file:'
        FocusControl = CredFilePathEdit
      end
      object CredFileProfileLbl: TUiLabel
        Left = 8
        Top = 46
        Height = 13
        Caption = '&Profile name:'
        FocusControl = CredFileProfileEdit
      end
      object CredFilePathEdit: TUiEdit
        Left = 8
        Top = 17
        Width = 239
        Height = 21
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
      object CredFileProfileEdit: TUiEdit
        Left = 8
        Top = 63
        Width = 239
        Height = 21
        TabOrder = 1
        OnChange = SomethingChangedClick
      end
    end
    object EnvVarsPanel: TUiActivePanel
      object EnvVarsLbl: TUiLabel
        Left = 8
        Top = 0
        Width = 239
        Height = 26
        Caption = 'Load access keys from AWS_* environment variables or credentials file.'
        WordWrap = True
      end
    end
  end
  object BucketEdit: TUiEdit
    Left = 8
    Top = 163
    Width = 239
    Height = 21
    TabOrder = 2
    OnChange = SomethingChangedClick
  end
  object DescriptionEdit: TUiMemo
    Left = 8
    Top = 209
    Width = 239
    Height = 92
    ScrollBars = ssVertical
    TabOrder = 3
    OnChange = SomethingChangedClick
  end
end
