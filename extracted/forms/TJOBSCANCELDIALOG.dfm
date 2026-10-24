object JobsCancelDialog: TJobsCancelDialog
  Caption = '%'
  ClientHeight = 85
  ClientWidth = 209
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object DescLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '%'
  end
  object ProgressBar: TUiProgressBar
    Left = 8
    Top = 25
    Width = 193
    Height = 17
    State = pbsMarquee
    TabOrder = 0
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 46
    Width = 209
    TabOrder = 1
    object CancelBtn: TUiCancelBtn
    end
  end
  object Timer: TTimer
    Enabled = False
    Interval = 500
    OnTimer = TimerTimer
    Left = 8
    Top = 8
  end
end
